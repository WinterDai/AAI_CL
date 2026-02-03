"""
ContextAgent - v9.0 Multi-Round Progressive Model with Resume Support

重构架构（Chain of Thought + 分段生成 + 断点恢复）：
- System Prompt: claude.md（合并 global_rules + 角色定义）
  - Round 1: 使用开头到Section 1
  - Round 2-4: 使用对应section的规则
  - Round 5: 使用完整prompt
- 多轮对话结构：
  Round 1: 分析理解（Chain of Thought）
  Round 2: 生成 Section 1 (Parsing Logic)
  Round 3: 生成 Section 2 (Check Logic)
  Round 4: 生成 Section 3 (Waiver Logic)
  Round 5: 生成 Section 4 (Implementation Guide)
- 使用 XML 标签结构化输入输出
- 断点恢复：自动检测已完成round并跳过
- 质量验证：检查TODO残留、section完整性等
- 输出：<item_id>_ItemSpec.md

符合 protocols/ 定义的 Agent 接口:
- 继承 BaseAgent
- 实现 process() 方法
- 返回 AgentResult
"""

import json
import logging
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Callable

# 修正导入路径
import sys
from pathlib import Path
# 添加当前 Agents 目录到路径 (用于 from Agents.xxx 导入)
_agents_dir = Path(__file__).parent.parent  # Agentic-AI/Agents
if str(_agents_dir) not in sys.path:
    sys.path.insert(0, str(_agents_dir))
# 添加 Agentic-AI 根目录到路径 (用于 from protocols 导入)
_root_dir = _agents_dir.parent  # Agentic-AI
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

# 导入协议
from protocols import BaseAgent, AgentResult

# LangChain imports for Phase 1-3
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Phase 4 imports
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableLambda
from langchain_core.callbacks import BaseCallbackHandler
from typing import Iterator, Any
from pydantic import BaseModel, Field
from typing import Optional

# 导入 LLM Skill (fallback)
try:
    from common.skills.llm_skill import get_llm_skill
except ImportError:
    from agents.common.skills.llm_skill import get_llm_skill

logger = logging.getLogger(__name__)


# Phase 3: Pydantic models for structured output
class AnalysisOutput(BaseModel):
    """Round 1 分析输出结构"""
    content: str = Field(description="分析内容，包含step-by-step推理")

class Section1Output(BaseModel):
    """Round 2 Section 1 (Parsing Logic) 输出结构"""
    content: str = Field(description="Section 1完整内容，Markdown格式")

class Section2Output(BaseModel):
    """Round 3 Section 2 (Check Logic) 输出结构"""
    content: str = Field(description="Section 2完整内容，Markdown格式")

class Section3Output(BaseModel):
    """Round 4 Section 3 (Waiver Logic) 输出结构"""
    content: str = Field(description="Section 3完整内容，Markdown格式")

class Section4Output(BaseModel):
    """Round 5 Section 4 (Implementation Guide) 输出结构"""
    content: str = Field(description="Section 4完整内容，Markdown格式")


# Phase 5: Custom callback handler for progress tracking
class ProgressCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler for progress tracking and streaming output
    
    Provides visibility into chain execution without blocking the pipeline.
    """
    
    def __init__(self, activity_logger=None):
        super().__init__()
        self.activity_logger = activity_logger or print
        self.current_round = None
    
    def on_chain_start(self, serialized: dict, inputs: dict, **kwargs: Any) -> None:
        """Called when chain starts"""
        round_name = kwargs.get('name', 'Unknown')
        self.current_round = round_name
        self.activity_logger(f"    [Callback] Chain started: {round_name}")
    
    def on_chain_end(self, outputs: dict, **kwargs: Any) -> None:
        """Called when chain ends"""
        if self.current_round:
            output_size = len(str(outputs)) if outputs else 0
            self.activity_logger(f"    [Callback] Chain completed: {self.current_round} ({output_size} chars)")
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when chain encounters error"""
        if self.current_round:
            self.activity_logger(f"    [Callback] Chain error: {self.current_round} - {error}")
    
    def on_llm_start(self, serialized: dict, prompts: list, **kwargs: Any) -> None:
        """Called when LLM starts"""
        self.activity_logger(f"    [Callback] LLM invocation started (prompts: {len(prompts)})")
    
    def on_llm_end(self, response, **kwargs: Any) -> None:
        """Called when LLM ends"""
        self.activity_logger(f"    [Callback] LLM invocation completed")


# Phase 4: Custom Runnable wrapper for JEDAI client
class JedaiLLMRunnable(Runnable):
    """LangChain Runnable wrapper for JEDAI client
    
    Enables LangChain chain integration while using custom JEDAI endpoint.
    """
    
    def __init__(self, jedai_client, system_prompt: str, round_name: str, llm_config: dict):
        super().__init__()
        self.jedai_client = jedai_client
        self.system_prompt = system_prompt
        self.round_name = round_name
        self.llm_config = llm_config
    
    def invoke(self, input: str, config=None) -> str:
        """Synchronous invoke - not supported, raises error"""
        raise NotImplementedError("JedaiLLMRunnable only supports async invoke")
    
    async def ainvoke(self, input: str, config=None) -> str:
        """Async invoke - calls JEDAI client (sync) in event loop"""
        import asyncio
        
        # Extract user_prompt from input (can be string or dict)
        user_prompt = input if isinstance(input, str) else input.get('user_prompt', str(input))
        
        # Prepare messages in JEDAI format
        messages = [{"role": "user", "content": user_prompt}]
        
        # Call JEDAI with retry logic (3 attempts with exponential backoff)
        # Note: JedaiClient.chat() is synchronous, not async
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # JEDAI client is synchronous - call directly without await
                response = self.jedai_client.chat(
                    messages=messages,
                    system=self.system_prompt,
                    model=self.llm_config.get("model", "claude-sonnet-4-5"),
                    temperature=self.llm_config.get("temperature", 0.7),
                    max_tokens=self.llm_config.get("max_tokens", 16000)
                )
                return response.content
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"[{self.round_name}] LLM call failed after {max_retries} attempts: {e}")
                    raise
                
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"[{self.round_name}] Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        
        raise RuntimeError(f"[{self.round_name}] LLM call failed after all retries")


class ContextAgent(BaseAgent):
    """
    ContextAgent v9.0 - 多轮渐进式模型 + 断点恢复
    
    架构（5 轮对话）：
    - Round 1: 分析理解（Chain of Thought）- 识别信息类别
    - Round 2: 生成 Parsing Logic - 填充模板 Section 1
    - Round 3: 生成 Check Logic - 填充模板 Section 2
    - Round 4: 生成 Waiver Logic - 填充模板 Section 3
    - Round 5: 生成 Implementation Guide - 填充模板 Section 4
    - 使用 XML 标签结构化每轮输入输出
    - 保留所有中间结果供 debug
    - 支持断点恢复（检测已完成round并跳过）
    - 质量验证（TODO残留、结构完整性检查）
    """
    
    def __init__(
        self,
        debug_mode: bool = False,
        llm_config: Optional[Dict] = None,
        activity_handler: Optional[Callable[[str], None]] = None,
        setting_sources: Optional[list[str]] = None,
    ):
        """初始化 ContextAgent"""
        default_llm_config = {
            "model": "claude-sonnet-4-5",
            "temperature": 0.0,
            "max_tokens": 16384,
        }
        
        super().__init__(
            llm_config=llm_config or default_llm_config,
            setting_sources=setting_sources,
            activity_handler=activity_handler,
        )
        
        self.debug_mode = debug_mode
        self._llm_skill = None
        self._langchain_llm = None  # Phase 1: LangChain ChatOpenAI instance
        self._chains = {}  # Phase 4: Store RunnableSequence chains for each round
        self._callback_handler = None  # Phase 5: Progress callback handler
        
        # 文件路径
        self._context_dir = Path(__file__).parent
        self._claude_prompt_path = self._context_dir / "claude.md"
        self._user_prompt_path = self._context_dir / "user_prompt.md"
        self._template_path = self._context_dir / "ItemSpec_Template_EN.md"
    
    def _default_system_prompt(self) -> str:
        """返回默认系统 Prompt（BaseAgent 要求）"""
        return "You are a Context Agent for generating ItemSpec documents."
    
    def _log_activity(self, message: str):
        """输出 Activity 日志"""
        if self.activity_handler:
            self.activity_handler(message)
        print(message)
    
    def _debug_log(self, title: str, data: Any):
        """Debug 模式下输出中间结果"""
        if self.debug_mode:
            print(f"\n=== {title} ===")
            if isinstance(data, dict):
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(data)
    
    def _build_chain(self, system_prompt: str, round_name: str) -> Runnable:
        """Phase 4-5: 构建LangChain RunnableSequence chain with callbacks
        
        Chain structure: user_prompt -> JEDAI LLM -> output
        
        Args:
            system_prompt: 系统提示（注入到LLM wrapper中）
            round_name: 轮次名称（用于日志）
        
        Returns:
            Runnable chain with callback support
        """
        # Check cache first
        cache_key = f"{round_name}_{hash(system_prompt)}"
        if cache_key in self._chains:
            return self._chains[cache_key]
        
        # Initialize JEDAI client if needed
        if not self._llm_skill:
            try:
                from common.jedai_client import JedaiClient
                self._llm_skill = JedaiClient()
                logger.info("[Chain] Initialized JEDAI client")
            except Exception as e:
                logger.error(f"[Chain] Failed to initialize JEDAI client: {e}")
                raise RuntimeError(f"JEDAI initialization failed: {e}") from e
        
        # Phase 5: Initialize callback handler if needed
        if not self._callback_handler:
            self._callback_handler = ProgressCallbackHandler(activity_logger=self._log_activity)
            logger.info("[Chain] Initialized callback handler")
        
        # Build chain: input -> JEDAI LLM -> output
        llm_runnable = JedaiLLMRunnable(
            jedai_client=self._llm_skill,
            system_prompt=system_prompt,
            round_name=round_name,
            llm_config=self.llm_config
        )
        
        # Simple chain: passthrough -> LLM
        chain = RunnablePassthrough() | llm_runnable
        
        # Cache the chain
        self._chains[cache_key] = chain
        logger.info(f"[Chain] Built chain for {round_name}")
        
        return chain
    
    async def _llm_call_single(self, system_prompt: str, user_prompt: str, round_name: str, 
                              output_model: Optional[BaseModel] = None) -> str:
        """Phase 4-5: LLM调用 - 使用LangChain RunnableSequence chain with callbacks
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            round_name: 轮次名称
            output_model: 可选的Pydantic模型（Phase 3特性，Phase 4-5保留）
        
        Phase 1-3: Template-based prompts + Pydantic models + JEDAI client
        Phase 4: Integrated LangChain RunnableSequence for better composability
        Phase 5: Added callback handlers for progress tracking (retry logic in JedaiLLMRunnable)
        """
        self._log_activity(f"    [LLM] Calling LLM for {round_name}...")
        
        # Phase 4-5: Build and execute chain with callbacks
        chain = self._build_chain(system_prompt, round_name)
        
        # Phase 3: 如果指定了output_model，添加JSON输出指令
        if output_model:
            json_instruction = """

Output your response as valid JSON matching this schema:
{
  "content": "your complete response here in markdown format"
}

Ensure the JSON is valid and the 'content' field contains your full markdown response."""
            user_prompt_enhanced = user_prompt + json_instruction
            logger.info(f"[Phase 3] Requesting structured JSON output for {round_name}")
        else:
            user_prompt_enhanced = user_prompt
        
        # Phase 4-5: Execute chain with callback support (retry logic in JedaiLLMRunnable)
        try:
            # Invoke chain with callbacks enabled
            config = {"callbacks": [self._callback_handler]} if self._callback_handler else None
            response = await chain.ainvoke(user_prompt_enhanced, config=config)
            self._log_activity(f"    [LLM] [OK] Response received ({len(response)} chars)")
            return response
        except Exception as e:
            logger.error(f"[{round_name}] Chain execution failed: {e}")
            raise
    
    def _load_yaml_config(self, config_path: str) -> Dict:
        """加载 YAML 配置文件（带异常处理）"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                raise ValueError(f"YAML file is empty or invalid: {config_path}")
            
            if not isinstance(config, dict):
                raise ValueError(f"YAML must be a dictionary, got {type(config).__name__}")
            
            return config
        
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parsing error in {config_path}: {e}") from e
        except UnicodeDecodeError as e:
            raise ValueError(f"File encoding error in {config_path}: {e}") from e
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {config_path}")
    
    def _load_prompt_file(self, file_path: Path) -> str:
        """加载 prompt 文件内容"""
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_xml_content(self, text: str, tag: str, use_pydantic: bool = False) -> str:
        """Phase 3: 从 XML 标签中提取内容（支持Pydantic结构化输出）
        
        Args:
            text: 响应文本
            tag: XML标签名
            use_pydantic: 是否尝试使用Pydantic解析（Phase 3特性）
        
        Returns:
            提取的内容字符串
        """
        import re
        
        # Phase 3: 尝试Pydantic结构化输出（如果启用）
        if use_pydantic:
            try:
                # 尝试JSON解析（Pydantic输出格式）
                import json
                data = json.loads(text)
                if 'content' in data:
                    logger.info(f"[Phase 3] Pydantic structured output parsed successfully for <{tag}>")
                    return data['content'].strip()
            except (json.JSONDecodeError, KeyError, TypeError):
                logger.debug(f"[Phase 3] Pydantic parsing failed, falling back to XML extraction for <{tag}>")
        
        # Fallback: 传统XML提取
        pattern = f"<{tag}>(.*?)</{tag}>"
        matches = re.findall(pattern, text, re.DOTALL)
        
        if len(matches) == 0:
            logger.warning(f"No <{tag}> tag found, returning full text")
            return text.strip()
        elif len(matches) > 1:
            logger.warning(f"Multiple <{tag}> tags found ({len(matches)}), using first match")
            return matches[0].strip()
        else:
            return matches[0].strip()
    
    def _build_round1_prompt(self, config: Dict, user_prompt_content: str) -> str:
        """Phase 2: 构建 Round 1 prompt using ChatPromptTemplate
        
        注入结构：
        - System Prompt: claude.md (Role + Core Principles + Global Rules)
        - User Prompt: user_prompt.md (通用部分，不含Section 1-4具体指导)
        - Task: Round 1分析任务
        - Configuration: YAML配置（不含实际input_files路径）
        """
        description = config.get('description', '')
        requirements = config.get('requirements', {})
        waivers = config.get('waivers', {})
        # 不传入实际input_files，只显示数量
        input_files_count = len(config.get('input_files', []))
        
        yaml_content = f"""description: {description}
requirements:
  value: {requirements.get('value', 'N/A')}
  pattern_items: {requirements.get('pattern_items', [])}
input_files: [{input_files_count} file(s) configured]
waivers:
  value: {waivers.get('value', 'N/A')}
  waive_items: {waivers.get('waive_items', [])}"""
        
        # Phase 2: Use template with variables
        template = """<!-- ========================================
     USER PROMPT: ItemSpec Generation Guide
     (From user_prompt.md)
========================================= -->

{user_prompt_content}

<!-- ========================================
     TASK: Round 1 - Analysis
========================================= -->

<task>
Analyze the checker requirements and identify what information needs to be extracted.
</task>

<!-- ========================================
     CONFIGURATION: YAML Input
========================================= -->

<configuration>
```yaml
{yaml_content}
```
</configuration>

<!-- ========================================
     INSTRUCTIONS: Analysis Steps
========================================= -->

<instructions>
Based on the description "{description}", perform step-by-step analysis:

1. **Identify Key Entities**: What are the main subjects mentioned? (e.g., "netlist", "spef", "version")

2. **Determine Information Categories**: What types of information validate "correctness"?
   - File loading status?
   - Version information?
   - Format validation?
   - Other domain-specific data?

3. **List Required Fields**: For each category, what specific fields are needed?
   - Example: Version info needs → tool_name, version_number, timestamp

4. **Design Data Structure**: How should parsed_fields be organized?
   - Group by file type or by validation aspect?
   - What metadata is needed (source_file, line_number, etc.)?

5. **Identify Validation Items**: Based on the information categories, what needs to be validated? (typically 2-6 items)

6. **Determine Pattern Matching Needs**: Which validation items require pattern matching vs. existence checks?

7. **Consider Waiver Scenarios**: When might this check legitimately fail?
   - Different design stages?
   - Legacy data?
   - Special circumstances?

Think step-by-step and be specific. Output your analysis inside <analysis></analysis> tags.
</instructions>"""
        
        return template.format(
            user_prompt_content=user_prompt_content,
            yaml_content=yaml_content,
            description=description
        )
    
    def _build_round2_prompt(self, analysis: str, template_section1: str, user_prompt_section1: str) -> str:
        """Phase 2: 构建 Round 2 prompt using template
        
        注入结构：
        - System Prompt: claude.md (Section 1相关规则)
        - User Prompt: user_prompt.md (Section 1指导)
        - Task: 生成Section 1
        - Context: Round 1分析结果 + Section 1模板
        """
        template = """<!-- ========================================
     USER PROMPT: Section 1 Guidance
     (From user_prompt.md)
========================================= -->

{user_prompt_section1}

<!-- ========================================
     TASK: Round 2 - Generate Section 1
========================================= -->

<task>
Generate Section 1 (Parsing Logic) of the ItemSpec based on your analysis.
</task>

<!-- ========================================
     CONTEXT: Previous Analysis
========================================= -->

<previous_analysis>
{analysis}
</previous_analysis>

<!-- ========================================
     TEMPLATE: Section 1 Structure
========================================= -->

<template_section>
{template_section1}
</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Parsing Logic section following these requirements:

1. **Information Categories**: Use the categories you identified in the analysis
   - Create subsection 1.1, 1.2, etc. for each category
   - Each subsection should have: Purpose + Key Fields

2. **Field Definitions**: For each field, specify:
   - What it represents (semantic meaning)
   - Data type (string, number, boolean)
   - How to identify it in input files

3. **Data Structure Example**: Provide a complete parsed_fields structure showing:
   - Grouping by category
   - All fields with example values
   - Metadata fields (source_file, line_number, matched_content)

4. **Remove Template Comments**: Delete all `<!-- -->` comments and `{{TODO: ...}}` markers

5. **Language**: Entire output must be in English

Output the complete Section 1 inside <section1></section1> tags.
</instructions>"""
        
        return template.format(
            user_prompt_section1=user_prompt_section1,
            analysis=analysis,
            template_section1=template_section1
        )
    
    def _build_round3_prompt(self, section1: str, analysis: str, template_section2: str, user_prompt_section2: str) -> str:
        """Phase 2: 构建 Round 3 prompt using template
        
        注入结构：
        - System Prompt: claude.md (Section 2相关规则)
        - User Prompt: user_prompt.md (Section 2指导)
        - Task: 生成Section 2
        - Context: Section 1 + Round 1分析 + Section 2模板
        """
        template = """<!-- ========================================
     USER PROMPT: Section 2 Guidance
     (From user_prompt.md)
========================================= -->

{user_prompt_section2}

<!-- ========================================
     TASK: Round 3 - Generate Section 2
========================================= -->

<task>
Generate Section 2 (Check Logic) of the ItemSpec.
</task>

<!-- ========================================
     CONTEXT: Section 1 (Parsing Logic)
========================================= -->

<section1_parsing_logic>
{section1}
</section1_parsing_logic>

<!-- ========================================
     CONTEXT: Analysis Reference
========================================= -->

<analysis_reference>
{analysis}
</analysis_reference>

<!-- ========================================
     TEMPLATE: Section 2 Structure
========================================= -->

<template_section>
{template_section2}
</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Check Logic section following these requirements:

1. **Validation Items**: Define 2-6 validation items based on your analysis
   - Each item validates one aspect from Parsing Logic
   - Create subsection 2.1, 2.2, etc.

2. **For Each Validation Item**, specify:
   - Item name and description
   - Completeness criteria (what fields must be present)
   - Whether pattern matching is needed
   - Expected behavior on PASS/FAIL

3. **Pattern Matching Correspondence**:
   - If requirements.value > 0, specify which items need pattern matching
   - Define the order correspondence with requirements.pattern_items
   - Items not requiring pattern matching are skipped in pattern_items list

4. **Overall Pass/Fail Logic**:
   - Define when checker returns PASS
   - Define when checker returns FAIL
   - Consider edge cases

5. **Remove Template Comments**: Delete all instructional text

Output the complete Section 2 inside <section2></section2> tags.
</instructions>"""
        
        return template.format(
            user_prompt_section2=user_prompt_section2,
            section1=section1,
            analysis=analysis,
            template_section2=template_section2
        )
    
    def _build_round4_prompt(self, section1: str, section2: str, analysis: str, template_section3: str, user_prompt_section3: str) -> str:
        """Phase 2: 构建 Round 4 prompt using template
        
        注入结构：
        - System Prompt: claude.md (Section 3相关规则)
        - User Prompt: user_prompt.md (Section 3指导)
        - Task: 生成Section 3
        - Context: Section 1+2 + Round 1分析 + Section 3模板
        """
        template = """<!-- ========================================
     USER PROMPT: Section 3 Guidance
     (From user_prompt.md)
========================================= -->

{user_prompt_section3}

<!-- ========================================
     TASK: Round 4 - Generate Section 3
========================================= -->

<task>
Generate Section 3 (Waiver Logic) of the ItemSpec.
</task>

<!-- ========================================
     CONTEXT: Previous Sections
========================================= -->

<previous_sections>
Section 1 (Parsing Logic):
{section1}

Section 2 (Check Logic):
{section2}
</previous_sections>

<!-- ========================================
     CONTEXT: Analysis Reference
========================================= -->

<analysis_reference>
{analysis}
</analysis_reference>

<!-- ========================================
     TEMPLATE: Section 3 Structure
========================================= -->

<template_section>
{template_section3}
</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Waiver Logic section following these requirements:

1. **Waivable Scenarios**: Identify 2-4 common scenarios where failures are acceptable
   - Consider different design stages (synthesis, P&R, signoff)
   - Think about regression testing with historical data
   - Account for legacy formats or special cases

2. **For Each Scenario**, specify:
   - Scenario name and description
   - Typical waiver reason (business justification)
   - Matching keywords for waivers.waive_items
   - Which validation items from Section 2 can be waived

3. **Waiver Modes Documentation**:
   - Global Mode (waivers.value=0): Behavior and use cases
   - Selective Mode (waivers.value>0): Matching strategy and application

4. **Implementation Guidance**:
   - Pattern matching strategies (exact, wildcard, regex)
   - How to link waivers to validation items
   - Traceability requirements

5. **Remove Template Comments**: Delete all instructional text

Output the complete Section 3 inside <section3></section3> tags.
</instructions>"""
        
        return template.format(
            user_prompt_section3=user_prompt_section3,
            section1=section1,
            section2=section2,
            analysis=analysis,
            template_section3=template_section3
        )
    
    def _build_round5_prompt(self, section1: str, section2: str, section3: str, template_section4: str, user_prompt_section4: str) -> str:
        """Phase 2: 构建 Round 5 prompt using template
        
        注入结构：
        - System Prompt: claude.md (完整规则)
        - User Prompt: user_prompt.md (Section 4指导 + 质量标准 + 示例推理)
        - Task: 生成Section 4
        - Context: Section 1+2+3摘要 + Section 4模板
        """
        # 提取前3个section的摘要（v9.1优化）
        summary1 = self._extract_section_summary(section1, "Section 1")
        summary2 = self._extract_section_summary(section2, "Section 2")
        summary3 = self._extract_section_summary(section3, "Section 3")
        
        template = """<!-- ========================================
     USER PROMPT: Section 4 Guidance & Quality Criteria
     (From user_prompt.md)
========================================= -->

{user_prompt_section4}

<!-- ========================================
     TASK: Round 5 - Generate Section 4
========================================= -->

<task>
Generate Section 4 (Implementation Guide) of the ItemSpec, ensuring overall quality.
</task>

<!-- ========================================
     CONTEXT: Previous Sections Summary
========================================= -->

<previous_sections_summary>
Section 1 Summary: {summary1}

Section 2 Summary: {summary2}

Section 3 Summary: {summary3}
</previous_sections_summary>

<!-- ========================================
     TEMPLATE: Section 4 Structure
========================================= -->

<template_section>
{template_section4}
</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Implementation Guide section following these requirements:

1. **Data Source Inference**: Based on previous sections, identify where to find the information
   - Infer from field types and validation requirements
   - Consider typical EDA tool outputs and log structures
   - List primary and fallback data sources

2. **Search Strategy**: Recommend practical extraction approaches
   - Keywords to search for in logs/files
   - Parsing patterns and regular expressions
   - Multi-stage extraction if needed

3. **Special Scenarios**: Document edge cases and exceptions
   - Missing file handling
   - Format variations across tools/versions
   - Fallback strategies when primary source unavailable

4. **Implementation Hints**: Practical guidance for downstream implementation
   - Common pitfalls to avoid
   - Performance considerations
   - Debugging tips

5. **Quality Check**: Ensure the complete ItemSpec meets all quality criteria
   - Semantic consistency across all sections
   - Practical implementability
   - Coverage of common scenarios
   - Adherence to framework rules

Output the complete Section 4 inside <section4></section4> tags.
</instructions>"""
        
        return template.format(
            user_prompt_section4=user_prompt_section4,
            summary1=summary1,
            summary2=summary2,
            summary3=summary3,
            template_section4=template_section4
        )
    
    def _load_template_sections(self, template_path: Path) -> Dict[str, str]:
        """加载模板并按section分割（增强边界检查）"""
        template_content = self._load_prompt_file(template_path)
        
        # 按 ## 数字. 分段
        import re
        sections = re.split(r'\n## (\d+)\.', template_content)
        
        # 分割结果: [header, '1', section1_content, '2', section2_content, ...]
        result = {"header": sections[0] if len(sections) > 0 else ""}
        
        # 提取各section
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_num = sections[i]
                section_content = sections[i + 1]
                result[f"section{section_num}"] = f"## {section_num}.{section_content}"
        
        # 验证必需的sections
        required = ["section1", "section2", "section3", "section4"]
        for sec in required:
            if sec not in result:
                raise ValueError(f"Template missing required {sec}")
        
        return result
    
    def _extract_claude_section(self, section_range: str) -> str:
        """从 claude.md 提取指定章节内容
        
        Args:
            section_range: '1-' (开头到Section 1结束) | '2' | '3' | '4'
        
        Returns:
            提取的章节内容
        """
        claude_content = self._load_prompt_file(self._claude_prompt_path)
        lines = claude_content.split('\n')
        
        # 找到各个 ## 数字. 的位置
        section_markers = {}
        for i, line in enumerate(lines):
            if line.startswith('## 1. Type System'):
                section_markers['1'] = i
            elif line.startswith('## 2. Logic Definitions'):
                section_markers['2'] = i
            elif line.startswith('## 3. Quality Checklist'):
                section_markers['3'] = i
            elif line.startswith('## Output Format Requirements'):
                section_markers['output'] = i
        
        # 根据 section_range 提取
        if section_range == '1-':
            # 从开头到 Section 1 结束（Section 2 开始前）
            end_line = section_markers.get('2', len(lines))
            return '\n'.join(lines[:end_line])
        elif section_range == '2':
            # Section 2 完整内容
            start = section_markers.get('2', 0)
            end = section_markers.get('3', len(lines))
            return '\n'.join(lines[start:end])
        elif section_range == '3':
            # Section 3 完整内容
            start = section_markers.get('3', 0)
            end = section_markers.get('output', len(lines))
            return '\n'.join(lines[start:end])
        elif section_range == '4':
            # Section 4 = Output Format Requirements
            start = section_markers.get('output', 0)
            return '\n'.join(lines[start:])
        else:
            raise ValueError(f"Invalid section_range: {section_range}")
    
    def _extract_section_summary(self, section_content: str, section_name: str) -> str:
        """提取Section的摘要（前500字符）
        
        Args:
            section_content: Section的完整内容
            section_name: Section名称（用于日志）
        
        Returns:
            Section的摘要
        """
        max_length = 500
        if len(section_content) <= max_length:
            return section_content
        
        # 截取前500字符并添加省略标记
        summary = section_content[:max_length].rsplit('\n', 1)[0]  # 在换行处截断
        return f"{summary}\n... (remaining {len(section_content) - len(summary)} chars omitted for brevity)"
    
    def _extract_user_prompt_sections(self, user_prompt_full: str) -> Dict[str, str]:
        """从 user_prompt.md 提取各阶段内容
        
        Args:
            user_prompt_full: 完整的user_prompt.md内容
        
        Returns:
            {
                'round1': 通用部分（除Section 1-4以外的内容）
                'section1': Section 1相关指导
                'section2': Section 2相关指导
                'section3': Section 3相关指导
                'section4': Section 4相关指导 + 质量标准 + 示例推理
            }
        """
        lines = user_prompt_full.split('\n')
        
        # 找到各个关键标记的位置
        markers = {}
        for i, line in enumerate(lines):
            if line.startswith('## Specific Instructions'):
                markers['specific_instructions'] = i
            elif line.startswith('### For Section 1 (Parsing Logic)'):
                markers['section1_start'] = i
            elif line.startswith('### For Section 2 (Check Logic)'):
                markers['section2_start'] = i
            elif line.startswith('### For Section 3 (Waiver Logic)'):
                markers['section3_start'] = i
            elif line.startswith('### For Section 4 (Implementation Guide)'):
                markers['section4_start'] = i
            elif line.startswith('## Quality Criteria'):
                markers['quality_criteria'] = i
            elif line.startswith('## Example Reasoning Path'):
                markers['example_reasoning'] = i
            elif line.startswith('## Important Notes'):
                markers['important_notes'] = i
        
        # Round 1: 只包含通用指导部分（从开头到"### For Section 1"之前）
        round1_end = markers.get('section1_start', len(lines))
        sections = {
            'round1': '\n'.join(lines[:round1_end])
        }
        
        # Section 1: Specific Instructions for Section 1
        section1_start = markers.get('section1_start', 0)
        section1_end = markers.get('section2_start', len(lines))
        sections['section1'] = '\n'.join(lines[section1_start:section1_end])
        
        # Section 2: Specific Instructions for Section 2
        section2_start = markers.get('section2_start', 0)
        section2_end = markers.get('section3_start', len(lines))
        sections['section2'] = '\n'.join(lines[section2_start:section2_end])
        
        # Section 3: Specific Instructions for Section 3
        section3_start = markers.get('section3_start', 0)
        section3_end = markers.get('section4_start', len(lines))
        sections['section3'] = '\n'.join(lines[section3_start:section3_end])
        
        # Section 4: Specific Instructions for Section 4 + Quality Criteria + Example Reasoning
        section4_start = markers.get('section4_start', 0)
        quality_end = markers.get('important_notes', len(lines))  # 到Important Notes前结束
        sections['section4'] = '\n'.join(lines[section4_start:quality_end])
        
        return sections
    
    def _validate_itemspec(self, content: str) -> list[str]:
        """验证生成的ItemSpec质量
        
        Returns:
            问题列表（空列表表示通过）
        """
        issues = []
        
        # 检查1: 是否有残留的TODO标记
        if '{TODO' in content or 'TODO:' in content:
            todo_count = content.count('{TODO') + content.count('TODO:')
            issues.append(f"Found {todo_count} unfilled TODO markers")
        
        # 检查2: 是否包含所有必需的Section
        required_sections = ['## 1. Parsing Logic', '## 2. Check Logic', 
                            '## 3. Waiver Logic', '## 4. Implementation Guide']
        for sec in required_sections:
            if sec not in content:
                issues.append(f"Missing required section: {sec}")
        
        # 检查4: 基本长度检查（太短说明生成不完整）
        if len(content) < 1000:
            issues.append(f"ItemSpec too short ({len(content)} chars), possibly incomplete")
        
        return issues
    
    def _check_resume_point(self, debug_dir: Path) -> tuple[int, Dict[str, str]]:
        """检查是否可以从断点恢复
        
        Returns:
            (resume_from_round, cached_results)
            resume_from_round: 1-5 表示从该round开始，0表示从头开始
            cached_results: 已完成round的结果
        """
        if not debug_dir or not debug_dir.exists():
            return (0, {})
        
        cached = {}
        
        # 检查 Round 5
        round5_file = debug_dir / "round5_section4.md"
        if round5_file.exists() and round5_file.stat().st_size > 100:
            cached['analysis'] = (debug_dir / "round1_analysis.md").read_text(encoding='utf-8')
            cached['section1'] = (debug_dir / "round2_section1.md").read_text(encoding='utf-8')
            cached['section2'] = (debug_dir / "round3_section2.md").read_text(encoding='utf-8')
            cached['section3'] = (debug_dir / "round4_section3.md").read_text(encoding='utf-8')
            cached['section4'] = round5_file.read_text(encoding='utf-8')
            logger.info("[Resume] All rounds completed, will assemble final ItemSpec")
            return (6, cached)  # 6表示直接组装
        
        # 检查 Round 4
        round4_file = debug_dir / "round4_section3.md"
        if round4_file.exists() and round4_file.stat().st_size > 100:
            cached['analysis'] = (debug_dir / "round1_analysis.md").read_text(encoding='utf-8')
            cached['section1'] = (debug_dir / "round2_section1.md").read_text(encoding='utf-8')
            cached['section2'] = (debug_dir / "round3_section2.md").read_text(encoding='utf-8')
            cached['section3'] = round4_file.read_text(encoding='utf-8')
            logger.info("[Resume] Resuming from Round 5")
            return (5, cached)
        
        # 检查 Round 3
        round3_file = debug_dir / "round3_section2.md"
        if round3_file.exists() and round3_file.stat().st_size > 100:
            cached['analysis'] = (debug_dir / "round1_analysis.md").read_text(encoding='utf-8')
            cached['section1'] = (debug_dir / "round2_section1.md").read_text(encoding='utf-8')
            cached['section2'] = round3_file.read_text(encoding='utf-8')
            logger.info("[Resume] Resuming from Round 4")
            return (4, cached)
        
        # 检查 Round 2
        round2_file = debug_dir / "round2_section1.md"
        if round2_file.exists() and round2_file.stat().st_size > 100:
            cached['analysis'] = (debug_dir / "round1_analysis.md").read_text(encoding='utf-8')
            cached['section1'] = round2_file.read_text(encoding='utf-8')
            logger.info("[Resume] Resuming from Round 3")
            return (3, cached)
        
        # 检查 Round 1
        round1_file = debug_dir / "round1_analysis.md"
        if round1_file.exists() and round1_file.stat().st_size > 100:
            cached['analysis'] = round1_file.read_text(encoding='utf-8')
            logger.info("[Resume] Resuming from Round 2")
            return (2, cached)
        
        logger.info("[Resume] No cached results, starting from Round 1")
        return (0, {})
    
    async def process(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        处理主入口（符合 BaseAgent 协议）
        
        Args:
            inputs: {"config_path": "path/to/item.yaml", "output_dir": "..."}
            
        Returns:
            AgentResult
        """
        config_path = inputs.get("config_path")
        output_dir = inputs.get("output_dir", "output")
        
        if not config_path:
            return AgentResult(
                result=None,
                messages=[],
                artifacts={},
                metadata={},
                status="failed",
                errors=["Missing config_path in inputs"]
            )
        
        try:
            # 执行主流程
            result = await self._run_pipeline(config_path, output_dir)
            
            return AgentResult(
                result="ItemSpec generation completed",
                messages=[],
                artifacts=result,
                metadata={"version": "v9.0", "model": "multi_round_progressive_with_resume"},
                status="success"
            )
        except Exception as e:
            logger.exception("Pipeline failed")
            return AgentResult(
                result=None,
                messages=[],
                artifacts={},
                metadata={},
                status="failed",
                errors=[str(e)]
            )
    
    async def _run_pipeline(self, config_path: str, output_dir: str) -> Dict:
        """
        完整流程：5轮渐进式生成 (v9.1 - 修复user_prompt注入)
        Round 1: 分析理解 → Round 2: Parsing Logic → Round 3: Check Logic → Round 4: Waiver Logic → Round 5: Implementation Guide
        """
        from datetime import datetime
        
        self._log_activity(f"\n[ContextAgent v9.1] Processing: {config_path}")
        
        # ===== Stage 1: 加载配置和 Prompt 文件 =====
        self._log_activity("\n[Stage 1] Loading Configuration and Prompts")
        
        # 1.1 加载 YAML 配置
        config = self._load_yaml_config(config_path)
        item_id = Path(config_path).stem
        self._log_activity(f"  [OK] Config loaded: {item_id}")
        self._debug_log("Config", config)
        
        # 1.2 加载 user_prompt.md（完整内容）
        user_prompt_full = self._load_prompt_file(self._user_prompt_path)
        self._log_activity(f"  [OK] User prompt loaded: {len(user_prompt_full)} chars")
        
        # 1.3 提取各阶段的user_prompt内容
        user_prompt_sections = self._extract_user_prompt_sections(user_prompt_full)
        self._log_activity(f"  [OK] User prompt sections extracted: {len(user_prompt_sections)} sections")
        
        template_sections = self._load_template_sections(self._template_path)
        self._log_activity(f"  [OK] Template sections loaded: {len(template_sections)} sections")
        
        # 创建输出目录和debug目录（带timestamp）
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 总是创建debug目录以支持断点恢复（非debug模式使用隐藏目录）
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        if self.debug_mode:
            debug_dir = output_path / f"debug_{timestamp}"
        else:
            # 非debug模式：使用隐藏目录.resume_cache支持断点恢复
            debug_dir = output_path / ".resume_cache" / timestamp
        
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # ===== Stage 1.5: 检查断点恢复 =====
        resume_from, cached = self._check_resume_point(debug_dir)
        
        analysis = cached.get('analysis', '')
        section1 = cached.get('section1', '')
        section2 = cached.get('section2', '')
        section3 = cached.get('section3', '')
        section4 = cached.get('section4', '')
        
        # ===== Stage 2: Round 1 - 分析理解（Chain of Thought） =====
        if resume_from <= 1:
            self._log_activity("\n[Stage 2] Round 1: Analysis (Chain of Thought)")
            
            # 使用精简的 system prompt（从开头到Section 1）
            system_prompt_r1 = self._extract_claude_section('1-')
            
            round1_prompt = self._build_round1_prompt(config, user_prompt_sections['round1'])
            self._log_activity(f"  [OK] Round 1 prompt built: {len(round1_prompt)} chars")
            
            response1 = await self._llm_call_single(system_prompt_r1, round1_prompt, "Round1_Analysis")
            analysis = self._extract_xml_content(response1, "analysis")
            self._log_activity(f"  [OK] Analysis completed: {len(analysis)} chars")
            self._debug_log("Round 1 Analysis", analysis[:500] + "...")
            
            # 保存 Round 1 debug
            if debug_dir:
                (debug_dir / "round1_system_prompt.md").write_text(system_prompt_r1, encoding='utf-8')
                (debug_dir / "round1_prompt.md").write_text(round1_prompt, encoding='utf-8')
                (debug_dir / "round1_response.md").write_text(response1, encoding='utf-8')
                (debug_dir / "round1_analysis.md").write_text(analysis, encoding='utf-8')
        else:
            self._log_activity(f"\n[Stage 2] Round 1: Skipped (cached)")
        
        # ===== Stage 3: Round 2 - 生成 Parsing Logic =====
        if resume_from <= 2:
            self._log_activity("\n[Stage 3] Round 2: Generate Parsing Logic")
            
            # 使用 Section 2 的 system prompt
            system_prompt_r2 = self._extract_claude_section('2')
            
            round2_prompt = self._build_round2_prompt(analysis, template_sections["section1"], user_prompt_sections['section1'])
            self._log_activity(f"  [OK] Round 2 prompt built: {len(round2_prompt)} chars")
            
            response2 = await self._llm_call_single(system_prompt_r2, round2_prompt, "Round2_ParsingLogic")
            section1 = self._extract_xml_content(response2, "section1")
            self._log_activity(f"  [OK] Section 1 generated: {len(section1)} chars")
            self._debug_log("Round 2 Section 1", section1[:500] + "...")
            
            # 保存 Round 2 debug
            if debug_dir:
                (debug_dir / "round2_system_prompt.md").write_text(system_prompt_r2, encoding='utf-8')
                (debug_dir / "round2_prompt.md").write_text(round2_prompt, encoding='utf-8')
                (debug_dir / "round2_response.md").write_text(response2, encoding='utf-8')
                (debug_dir / "round2_section1.md").write_text(section1, encoding='utf-8')
        else:
            self._log_activity(f"\n[Stage 3] Round 2: Skipped (cached)")
        
        # ===== Stage 4: Round 3 - 生成 Check Logic =====
        if resume_from <= 3:
            self._log_activity("\n[Stage 4] Round 3: Generate Check Logic")
            
            # 使用 Section 3 的 system prompt
            system_prompt_r3 = self._extract_claude_section('3')
            
            round3_prompt = self._build_round3_prompt(section1, analysis, template_sections["section2"], user_prompt_sections['section2'])
            self._log_activity(f"  [OK] Round 3 prompt built: {len(round3_prompt)} chars")
            
            response3 = await self._llm_call_single(system_prompt_r3, round3_prompt, "Round3_CheckLogic")
            section2 = self._extract_xml_content(response3, "section2")
            self._log_activity(f"  [OK] Section 2 generated: {len(section2)} chars")
            self._debug_log("Round 3 Section 2", section2[:500] + "...")
            
            # 保存 Round 3 debug
            if debug_dir:
                (debug_dir / "round3_system_prompt.md").write_text(system_prompt_r3, encoding='utf-8')
                (debug_dir / "round3_prompt.md").write_text(round3_prompt, encoding='utf-8')
                (debug_dir / "round3_response.md").write_text(response3, encoding='utf-8')
                (debug_dir / "round3_section2.md").write_text(section2, encoding='utf-8')
        else:
            self._log_activity(f"\n[Stage 4] Round 3: Skipped (cached)")
        
        # ===== Stage 5: Round 4 - 生成 Waiver Logic =====
        if resume_from <= 4:
            self._log_activity("\n[Stage 5] Round 4: Generate Waiver Logic")
            
            # 使用 Section 4 的 system prompt (Output Format Requirements)
            system_prompt_r4 = self._extract_claude_section('4')
            
            round4_prompt = self._build_round4_prompt(section1, section2, analysis, template_sections["section3"], user_prompt_sections['section3'])
            self._log_activity(f"  [OK] Round 4 prompt built: {len(round4_prompt)} chars")
            
            response4 = await self._llm_call_single(system_prompt_r4, round4_prompt, "Round4_WaiverLogic")
            section3 = self._extract_xml_content(response4, "section3")
            self._log_activity(f"  [OK] Section 3 generated: {len(section3)} chars")
            self._debug_log("Round 4 Section 3", section3[:500] + "...")
            
            # 保存 Round 4 debug
            if debug_dir:
                (debug_dir / "round4_system_prompt.md").write_text(system_prompt_r4, encoding='utf-8')
                (debug_dir / "round4_prompt.md").write_text(round4_prompt, encoding='utf-8')
                (debug_dir / "round4_response.md").write_text(response4, encoding='utf-8')
                (debug_dir / "round4_section3.md").write_text(section3, encoding='utf-8')
        else:
            self._log_activity(f"\n[Stage 5] Round 4: Skipped (cached)")
        
        # ===== Stage 6: Round 5 - 生成 Implementation Guide =====
        if resume_from <= 5:
            self._log_activity("\n[Stage 6] Round 5: Generate Implementation Guide")
            
            # 使用完整 system prompt（Section 4 需要全局理解）
            system_prompt_r5 = self._load_prompt_file(self._claude_prompt_path)
            
            round5_prompt = self._build_round5_prompt(section1, section2, section3, template_sections["section4"], user_prompt_sections['section4'])
            self._log_activity(f"  [OK] Round 5 prompt built: {len(round5_prompt)} chars")
            
            response5 = await self._llm_call_single(system_prompt_r5, round5_prompt, "Round5_ImplGuide")
            section4 = self._extract_xml_content(response5, "section4")
            self._log_activity(f"  [OK] Section 4 generated: {len(section4)} chars")
            self._debug_log("Round 5 Section 4", section4[:500] + "...")
            
            # 保存 Round 5 debug
            if debug_dir:
                (debug_dir / "round5_system_prompt.md").write_text(system_prompt_r5, encoding='utf-8')
                (debug_dir / "round5_prompt.md").write_text(round5_prompt, encoding='utf-8')
                (debug_dir / "round5_response.md").write_text(response5, encoding='utf-8')
                (debug_dir / "round5_section4.md").write_text(section4, encoding='utf-8')
        else:
            self._log_activity(f"\n[Stage 6] Round 5: Skipped (cached)")
        
        # ===== Stage 7: 组装最终 ItemSpec =====
        self._log_activity("\n[Stage 7] Assembling Final ItemSpec")
        
        # 组装完整文档
        itemspec_content = f"""# ItemSpec: {item_id}

{section1}

{section2}

{section3}

{section4}
"""
        
        # 替换占位符
        itemspec_content = itemspec_content.replace("{ITEM_ID}", item_id)
        itemspec_content = itemspec_content.replace("{DESCRIPTION}", config.get('description', ''))
        
        self._log_activity(f"  [OK] ItemSpec assembled: {len(itemspec_content)} chars")
        
        # ===== Stage 8: 质量验证 =====
        self._log_activity("\n[Stage 8] Quality Validation")
        
        validation_issues = self._validate_itemspec(itemspec_content)
        if validation_issues:
            error_msg = "\n".join([f"  [FAIL] {issue}" for issue in validation_issues])
            self._log_activity(f"\n[VALIDATION WARNING]\n{error_msg}")
            self._log_activity("  [WARN]  Will save ItemSpec with [NEEDS_REVIEW] marker")
            
            # 在文件名和内容中添加警告标记
            itemspec_filename = f"{item_id}_ItemSpec_NEEDS_REVIEW.md"
            warning_header = f"""<!-- 
==============================================
  WARNING: QUALITY VALIDATION FAILED
==============================================
Issues found:
{error_msg}

Please review and manually fix these issues before using this ItemSpec.
==============================================
-->

"""
            itemspec_content = warning_header + itemspec_content
        else:
            self._log_activity(f"  [OK] Quality validation passed")
            itemspec_filename = f"{item_id}_ItemSpec.md"
        
        # ===== Stage 9: 保存输出 =====
        self._log_activity("\n[Stage 9] Saving Output")
        
        # 保存 ItemSpec 文件（原子性写入）
        itemspec_path = output_path / itemspec_filename
        
        # 使用临时文件+原子替换保证写入完整性
        import tempfile
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                            dir=output_path, delete=False, 
                                            suffix='.tmp') as tmp_file:
                tmp_file.write(itemspec_content)
                tmp_path = tmp_file.name
            
            # 原子替换
            import shutil
            shutil.move(tmp_path, itemspec_path)
        except Exception as e:
            # 清理临时文件
            if 'tmp_path' in locals() and Path(tmp_path).exists():
                Path(tmp_path).unlink()
            raise RuntimeError(f"Failed to save ItemSpec: {e}") from e
        
        self._log_activity(f"  [OK] ItemSpec saved: {itemspec_path}")
        
        # 保存其他 debug 信息
        if debug_dir:
            with open(debug_dir / "config.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            
            self._log_activity(f"  [OK] Debug files saved: {debug_dir}")
        
        self._log_activity(f"\n[Complete] Output saved to: {output_path}")
        
        return {
            "itemspec_path": str(itemspec_path),
            "itemspec_content": itemspec_content,
            "item_id": item_id,
            "rounds": {
                "analysis": analysis,
                "section1": section1,
                "section2": section2,
                "section3": section3,
                "section4": section4
            }
        }


# CLI 入口
async def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python agent.py <config.yaml> [output_dir]")
        sys.exit(1)
    
    config_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./output"
    
    agent = ContextAgent(debug_mode=True)
    result = await agent.process({
        "config_path": config_path,
        "output_dir": output_dir
    })
    
    if result.status == "success":
        print(f"\n[OK] Success! ItemSpec generated:")
        print(f"  - Path: {result.artifacts.get('itemspec_path')}")
        print(f"  - Item ID: {result.artifacts.get('item_id')}")
    else:
        print(f"\n[FAIL] Failed: {result.errors}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
