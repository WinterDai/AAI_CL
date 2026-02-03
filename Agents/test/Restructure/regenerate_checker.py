"""
重新生成 Check_10_0_0_00_generated.py 使其与 aggressive 版本完全匹配
使用 CodeGen Agent v3.4
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加路径
agent_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(agent_root))

from agents.code_generation.agent import CodeGenerationAgent
from agents.code_generation.models import CodeGenInput


async def regenerate_checker():
    print('=' * 70)
    print('重新生成 IMP-10-0-0-00 Checker (与 Aggressive 版本匹配)')
    print('=' * 70)
    
    # 路径配置
    item_spec_path = agent_root / 'test' / 'ContextAgent' / 'IMP-10-0-0-00' / 'item_spec.json'
    log_file_path = agent_root / 'test' / 'IP_project_folder' / 'logs' / 'sta_post_syn.log'
    output_dir = Path(__file__).parent
    
    # 加载 item_spec
    print(f'\n加载 item_spec: {item_spec_path}')
    with open(item_spec_path, 'r', encoding='utf-8') as f:
        item_spec = json.load(f)
    
    print(f'  item_id: {item_spec["item_id"]}')
    print(f'  description: {item_spec["description"]}')
    
    # 加载 log_samples
    log_samples = {}
    if log_file_path.exists():
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_samples['sta_post_syn.log'] = f.read()
        print(f'  log sample: {log_file_path.name} ({len(log_samples["sta_post_syn.log"])} bytes)')
    
    # 构建输入
    codegen_input = CodeGenInput(
        item_spec=item_spec,
        log_samples=log_samples,
        output_dir=str(output_dir),
        debug_mode=True,
    )
    
    # 验证
    hard_errors = codegen_input.get_hard_errors()
    warnings = codegen_input.get_warnings()
    print(f'\n输入验证:')
    print(f'  Hard errors: {hard_errors or "None"}')
    print(f'  Warnings: {len(warnings) if warnings else 0} items')
    
    if hard_errors:
        print('❌ Cannot proceed due to hard errors')
        return None
    
    # 运行 CodeGen Agent
    print('\n' + '=' * 70)
    print('运行 CodeGenerationAgent...')
    print('=' * 70)
    
    agent = CodeGenerationAgent(debug_mode=True)
    
    # 保存System Prompt用于检查
    system_prompt = agent.system_prompt
    system_prompt_path = output_dir / 'system_prompt_claude.md'
    with open(system_prompt_path, 'w', encoding='utf-8') as f:
        f.write(system_prompt)
    print(f'\n💾 System Prompt已保存: {system_prompt_path}')
    print(f'   长度: {len(system_prompt)} 字符, {len(system_prompt.splitlines())} 行')
    
    result = await agent.process(codegen_input.to_dict())
    
    print(f'\n结果摘要:')
    print(f'  Status: {result.status}')
    print(f'  Validation: {result.artifacts.get("validation_result", "N/A")}')
    print(f'  Input Tokens: {result.metadata.get("input_tokens", 0)}')
    print(f'  Output Tokens: {result.metadata.get("output_tokens", 0)}')
    
    if result.errors:
        print(f'  ❌ Errors: {result.errors}')
    if result.warnings:
        print(f'  ⚠️ Warnings: {len(result.warnings)} items')
    
    # 保存生成的代码
    code = result.artifacts.get('code')
    if code:
        code_path = output_dir / 'Check_10_0_0_00_generated.py'
        with open(code_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f'\n✅ 生成的代码已保存:')
        print(f'  Path: {code_path}')
        print(f'  Lines: {len(code.splitlines())}')
    else:
        print('\n❌ 未能生成代码!')
    
    return result


if __name__ == '__main__':
    result = asyncio.run(regenerate_checker())
    if result and result.status == 'success':
        print('\n' + '=' * 70)
        print('✅ 代码生成成功！现在运行测试验证...')
        print('=' * 70)
        
        # 自动运行测试
        import subprocess
        test_result = subprocess.run(
            ['python', 'test_generated_all_types.py'],
            cwd=Path(__file__).parent,
            capture_output=False
        )
        
        if test_result.returncode == 0:
            print('\n🎉 所有测试通过！')
        else:
            print('\n⚠️ 测试失败，需要检查生成的代码')
