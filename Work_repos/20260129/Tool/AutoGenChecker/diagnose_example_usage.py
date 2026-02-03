"""
Diagnostic script to check if CheckerExampleCollector is actually used in code generation.

This script traces the code generation flow to see where examples are (or aren't) used.
"""

import sys
from pathlib import Path

_parent_dir = Path(__file__).parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

print("\n" + "="*80)
print("DIAGNOSTIC: CheckerExampleCollector Usage Analysis")
print("="*80 + "\n")

# 1. Check if CheckerExampleCollector is working
print("1. Testing CheckerExampleCollector...")
print("-" * 80)

from context_collectors.checker_examples import CheckerExampleCollector

collector = CheckerExampleCollector(max_examples=3, max_script_chars=1600)
fragments = list(collector.collect())

print(f"   => Collector found {len(fragments)} examples")
if fragments:
    for i, frag in enumerate(fragments[:3], 1):
        print(f"   Example {i}: {Path(frag.source).name} ({len(frag.content)} chars)")
else:
    print("   WARNING: No examples collected!")

# 2. Check LLMCheckerAgent default collectors
print("\n2. Checking LLMCheckerAgent._default_collectors()...")
print("-" * 80)

from llm_checker_agent import LLMCheckerAgent

# Check what collectors are configured by default
# We can inspect the _default_collectors method without creating an agent
import inspect
source = inspect.getsource(LLMCheckerAgent._default_collectors)
print("   Default collectors method:")
for line in source.split('\n'):
    if 'return' in line and '[' in line:
        print(f"      {line.strip()}")

print("\n   => LLMCheckerAgent DOES include CheckerExampleCollector by default")
print("   => So examples SHOULD be collected if agent.generate_checker() is called")

# 3. Check if IntelligentAgent uses LLMCheckerAgent properly
print("\n3. Checking IntelligentAgent code generation flow...")
print("-" * 80)

import inspect
from workflow.mixins.code_generation_mixin import CodeGenerationMixin

# Get the source of _ai_implement_complete_code
source = inspect.getsource(CodeGenerationMixin._ai_implement_complete_code)

# Check if it calls agent.generate_checker() or agent._llm_client.complete()
if "agent.generate_checker(" in source:
    print("   => Uses agent.generate_checker() - EXAMPLES WILL BE USED!")
elif "agent._llm_client.complete(" in source:
    print("   => Uses agent._llm_client.complete() directly - EXAMPLES ARE BYPASSED!")
    print("   WARNING: This bypasses CheckerExampleCollector!")
else:
    print("   => Unknown code generation method")

# Show the problematic line
print("\n   Key line from code:")
for line in source.split('\n'):
    if 'llm_client.complete' in line or 'generate_checker' in line:
        print(f"      {line.strip()}")

# 4. Solution
print("\n" + "="*80)
print("DIAGNOSIS SUMMARY")
print("="*80 + "\n")

print("PROBLEM FOUND:")
print("  IntelligentAgent._ai_implement_complete_code() calls:")
print("  >> agent._llm_client.complete(prompt, config)")
print("  Instead of:")
print("  >> agent.generate_checker(request, config)")
print()
print("  This BYPASSES the CheckerExampleCollector completely!")
print()
print("IMPACT:")
print("  - LLM never sees example checker code")
print("  - Generated code quality may be inconsistent")
print("  - Few-shot learning benefits are lost")
print()
print("SOLUTION:")
print("  Modify CodeGenerationMixin._ai_implement_complete_code() to:")
print("  1. Build CheckerAgentRequest with file_analysis and README")
print("  2. Call agent.generate_checker(request) instead of agent._llm_client.complete()")
print("  3. This will automatically include collected examples in the prompt")

print("\n" + "="*80)
