# -*- coding: utf-8 -*-
"""
ValidationAgent Full Debug Script

完整的 ValidationAgent 调试脚本，使用：
- test/Check_modules/10.0_STA_DCD_CHECK/inputs/items/IMP-10-0-0-00.yaml
- 标准化输出目录结构
- 完整的 README 和路径清单

输出到: test/Validation/{item_id}/
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Setup paths
_SCRIPT_DIR = Path(__file__).resolve().parent
_AGENT_DIR = _SCRIPT_DIR.parents[2]  # test/Validation/IMP-10-0-0-00 -> Agent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

# Configuration
ITEM_ID = "IMP-10-0-0-00"
OUTPUT_ROOT = _SCRIPT_DIR.parent  # test/Validation/


def print_section(title: str):
    """打印分节标题"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def run_validation_debug():
    """运行完整的 ValidationAgent 调试"""
    print_section(f"ValidationAgent Full Debug: {ITEM_ID}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"输出目录: {OUTPUT_ROOT / ITEM_ID}")
    
    # ========================================================================
    # Step 1: 加载测试数据
    # ========================================================================
    print_section("Step 1: 加载测试数据")
    
    from agents.validation.test_loader import TestDataLoader, load_dev_item
    from agents.validation.output_manager import ValidationOutputManager
    
    # 初始化加载器
    loader = TestDataLoader(agent_root=_AGENT_DIR, use_dev_data=True)
    
    # 检查路径
    print(f"Agent Root: {loader.agent_root}")
    print(f"Check Modules Root: {loader.check_modules_root}")
    
    # 加载 item.yaml
    item_config = loader.load_item_config(ITEM_ID)
    if not item_config:
        print(f"❌ 未找到 {ITEM_ID} 的 item.yaml")
        return False
    
    print(f"✅ 已加载 item.yaml: {item_config.source_path}")
    print(f"   Description: {item_config.description}")
    print(f"   Requirements: value={item_config.requirements_value}")
    print(f"   Pattern Items: {item_config.pattern_items}")
    print(f"   Waivers: value={item_config.waivers_value}")
    
    # ========================================================================
    # Step 2: 初始化输出管理器
    # ========================================================================
    print_section("Step 2: 初始化输出目录结构")
    
    output_mgr = ValidationOutputManager(OUTPUT_ROOT, ITEM_ID)
    output_mgr.initialize(archive_existing=True)
    
    paths = output_mgr.get_all_paths()
    print("已创建目录结构:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    # 复制 item.yaml
    item_yaml_path = Path(item_config.source_path)
    output_mgr.save_item_yaml(item_yaml_path)
    print(f"\n✅ 已复制 item.yaml 到 input/")
    
    # ========================================================================
    # Step 3: 加载 CodeGen 输出 (从 Orchestrator 测试目录)
    # ========================================================================
    print_section("Step 3: 加载 CodeGenAgent 输出")
    
    # 检查多个可能的位置
    possible_paths = [
        _AGENT_DIR / "test" / "Ochestrator" / ITEM_ID / "generated_checker.py",
        _AGENT_DIR / "test" / "CodeGen" / ITEM_ID / f"Check_{ITEM_ID.replace('-', '_').replace('IMP_', '')}.py",
    ]
    
    generated_code = None
    item_spec = None
    source_path = None
    
    for path in possible_paths:
        if path.exists():
            source_path = path
            break
    
    if source_path:
        print(f"发现已有 CodeGen 输出: {source_path}")
        with open(source_path, 'r', encoding='utf-8') as f:
            generated_code = f.read()
        print(f"✅ 已加载 checker 代码 ({len(generated_code)} chars)")
        
        # 尝试加载 item_spec
        spec_paths = [
            source_path.parent / "input_item_spec.json",
            source_path.parent / "codegen_debug.json",
        ]
        for spec_path in spec_paths:
            if spec_path.exists():
                with open(spec_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    item_spec = data.get("item_spec", data) if "item_spec" in data else data
                print(f"✅ 已加载 item_spec 从 {spec_path.name}")
                break
    else:
        print("未找到已有 CodeGen 输出，将构建 item_spec 并调用 CodeGenAgent...")
        
        # 构建 item_spec (从 item_config)
        item_spec = {
            "item_id": item_config.item_id,
            "description": item_config.description,
            "check_module": "IMP",
            "input_files": item_config.input_files,
            "requirements": {
                "value": item_config.requirements_value,
                "pattern_items": item_config.pattern_items,
            },
            "waivers": {
                "value": item_config.waivers_value,
                "waive_items": item_config.waive_items,
            },
        }
        
        # 运行 CodeGenerationAgent (注意类名)
        from agents.code_generation.agent import CodeGenerationAgent
        
        codegen_output_dir = _AGENT_DIR / "test" / "CodeGen" / ITEM_ID
        codegen_output_dir.mkdir(parents=True, exist_ok=True)
        
        codegen = CodeGenerationAgent(debug_mode=True)
        codegen_result = await codegen.process({
            "item_spec": item_spec,
            "output_dir": str(codegen_output_dir),
        })
        
        if codegen_result.status == "success" and codegen_result.result:
            generated_code = codegen_result.result
            print(f"✅ CodeGen 成功生成代码 ({len(generated_code)} chars)")
        else:
            print(f"❌ CodeGen 失败: {getattr(codegen_result, 'errors', 'Unknown error')}")
            return False
    
    # 保存到输出目录
    if generated_code:
        output_mgr.save_generated_code(generated_code)
        print("✅ 已保存 generated_checker.py 到 input/")
    
    if item_spec:
        output_mgr.save_item_spec(item_spec)
        print("✅ 已保存 item_spec.json 到 input/")
    
    # ========================================================================
    # Step 4: 运行 ValidationAgent
    # ========================================================================
    print_section("Step 4: 运行 ValidationAgent")
    
    from agents.validation.agent import ValidationAgent
    from agents.validation.models import ValidationInput
    
    # 准备验证输入
    validation_input = ValidationInput(
        generated_code=generated_code,
        item_spec=item_spec or item_config.to_dict(),
        log_samples=None,
    )
    
    # 创建 ValidationAgent
    validator = ValidationAgent(
        debug_mode=True,
        use_mock_llm=True,  # 使用 Mock LLM 进行快速测试
    )
    
    print("开始验证...")
    start_time = datetime.now()
    
    result = await validator.process({
        "generated_code": generated_code,
        "item_spec": item_spec or item_config.to_dict(),
    })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"✅ 验证完成 (耗时: {duration:.2f}s)")
    print(f"   Status: {result.status}")
    
    # ========================================================================
    # Step 5: 保存结果并生成 TestCase 文件
    # ========================================================================
    print_section("Step 5: 保存验证结果")
    
    # 从 result.artifacts 提取数据
    artifacts = result.artifacts or {}
    
    # 保存 TestCase 配置
    test_cases = artifacts.get("test_cases", [])
    for i, tc in enumerate(test_cases):
        if hasattr(tc, 'id'):
            tc_id = tc.id
            tc_type = tc.type_id
            tc_direction = tc.direction
            tc_config = {}
            if tc.config_override:
                tc_config = {
                    "requirements": tc.config_override.requirements,
                    "pattern_items": tc.config_override.pattern_items,
                }
                if tc.config_override.waivers:
                    tc_config["waivers"] = {
                        "value": tc.config_override.waivers.value,
                        "type": tc.config_override.waivers.type,
                    }
            output_mgr.save_test_case(tc_id, tc_type, tc_direction, tc_config)
    
    print(f"✅ 已保存 {len(test_cases)} 个 TestCase 配置")
    
    # 保存执行结果
    executions = artifacts.get("executions", [])
    for exec_result in executions:
        if hasattr(exec_result, 'test_case_id'):
            tc_id = exec_result.test_case_id
            
            # 生成模拟的 log 和 report
            log_content = f"""[{datetime.now().isoformat()}] TestCase: {tc_id}
Item: {ITEM_ID}
Status: {exec_result.actual_output if hasattr(exec_result, 'actual_output') else 'N/A'}
Duration: {exec_result.duration_ms if hasattr(exec_result, 'duration_ms') else 0}ms

Execution Log:
{exec_result.stdout if hasattr(exec_result, 'stdout') else '(no stdout)'}

Errors:
{exec_result.stderr if hasattr(exec_result, 'stderr') else '(no stderr)'}
"""
            log_path = output_mgr.save_execution_log(tc_id, log_content)
            
            report_content = f"""{exec_result.actual_output if hasattr(exec_result, 'actual_output') else 'N/A'}:{ITEM_ID}:{item_config.description}
TestCase: {tc_id}
Expected: {exec_result.expected_output if hasattr(exec_result, 'expected_output') else 'N/A'}
Actual: {exec_result.actual_output if hasattr(exec_result, 'actual_output') else 'N/A'}
"""
            report_path = output_mgr.save_execution_report(tc_id, report_content)
            
            # 记录执行结果
            output_mgr.record_execution_result(
                tc_id=tc_id,
                actual_output=exec_result.actual_output if hasattr(exec_result, 'actual_output') else "N/A",
                expected_output=exec_result.expected_output if hasattr(exec_result, 'expected_output') else "N/A",
                verdict=exec_result.verdict if hasattr(exec_result, 'verdict') else "UNKNOWN",
                log_path=log_path,
                report_path=report_path,
            )
    
    print(f"✅ 已保存 {len(executions)} 个执行日志和报告")
    
    # 保存验证结果
    validation_result = {
        "item_id": ITEM_ID,
        "status": result.status,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": duration,
        "summary": artifacts.get("summary", {}),
        "test_case_count": len(test_cases),
        "execution_count": len(executions),
    }
    
    # 添加统计
    if artifacts.get("aggregated"):
        agg = artifacts["aggregated"]
        validation_result["statistics"] = {
            "total": agg.total_tests if hasattr(agg, 'total_tests') else 0,
            "correct": agg.correct_count if hasattr(agg, 'correct_count') else 0,
            "incorrect": agg.incorrect_count if hasattr(agg, 'incorrect_count') else 0,
            "uncertain": agg.uncertain_count if hasattr(agg, 'uncertain_count') else 0,
            "invalid": agg.invalid_count if hasattr(agg, 'invalid_count') else 0,
        }
    
    output_mgr.save_validation_result(validation_result)
    print("✅ 已保存 validation_result.json")
    
    # 保存验证报告
    report_md = artifacts.get("report", "")
    if report_md:
        output_mgr.save_validation_report(report_md)
        print("✅ 已保存 validation_report.md")
    
    # 保存 CodeGen 反馈
    feedback = artifacts.get("feedback", {})
    if feedback:
        output_mgr.save_codegen_feedback(feedback)
        print("✅ 已保存 feedback_to_codegen.json")
    
    # ========================================================================
    # Step 6: 生成完整 README
    # ========================================================================
    print_section("Step 6: 生成 README.md")
    
    readme_path = output_mgr.generate_readme()
    print(f"✅ 已生成: {readme_path}")
    
    # ========================================================================
    # 最终输出
    # ========================================================================
    print_section("调试完成")
    
    print(f"输出目录: {output_mgr.item_dir}")
    print()
    print("生成的文件:")
    
    # 列出所有文件
    def list_files(dir_path: Path, prefix: str = ""):
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                print(f"{prefix}📁 {item.name}/")
                list_files(item, prefix + "  ")
            else:
                print(f"{prefix}📄 {item.name}")
    
    list_files(output_mgr.item_dir)
    
    print()
    print(f"查看详细报告: {output_mgr.item_dir / 'README.md'}")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(run_validation_debug())
    sys.exit(0 if success else 1)
