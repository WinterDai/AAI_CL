"""
LLM Skill - 统一 LLM 调用入口 (Singleton)

版本: v1.0.0 (2025-12-23)

职责:
- 统一 LLM API 调用入口
- Token 统计 (全局 + 按 Agent)
- 限流处理 (指数退避)
- 多 Provider 支持 (JEDAI / Anthropic)

使用方式:
    from agents.common.skills.llm_skill import get_llm_skill
    
    llm = get_llm_skill()
    response = await llm.chat(
        messages=[{"role": "user", "content": "Hello"}],
        system="You are helpful.",
        agent_id="context_agent"
    )
    print(response.content)
    print(llm.get_stats())  # 全局统计
"""

import os
import json
import asyncio
import random
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# 数据类
# ============================================================================

@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    stop_reason: str = "end_turn"
    raw_response: Any = None


@dataclass
class LLMStats:
    """Token 统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    call_count: int = 0
    error_count: int = 0
    last_call_time: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "last_call_time": self.last_call_time,
        }


# ============================================================================
# LLM Skill (Singleton)
# ============================================================================

class LLMSkill:
    """
    LLM 调用 Skill (Singleton)
    
    统一管理所有 Agent 的 LLM 调用，提供:
    - 单例模式: 复用连接和认证状态
    - Token 统计: 全局 + 按 Agent 分组
    - 限流处理: 指数退避重试
    - 多 Provider: JEDAI (优先) / Anthropic
    
    Example:
        llm = LLMSkill.get_instance()
        response = await llm.chat(
            messages=[{"role": "user", "content": "Hello"}],
            system="You are helpful.",
            agent_id="context_agent",
            model="claude-sonnet-4-5",  # 或使用别名 "sonnet", "opus" 等
            max_tokens=4096
        )
    
    支持的模型 (JEDAI - 37 种):
        Claude: claude-sonnet-4-5 (默认), claude-sonnet-4, claude-opus-4, claude-opus-4-1,
                claude-haiku-4-5, claude-3-7-sonnet, claude-3-5-sonnet, claude-3-opus
        Gemini: gemini-2-5-pro, gemini-2-5-flash, gemini-2-5-flash-lite, gemini-1-5-pro
        Llama:  meta-llama-3-1-8b/70b/405b-instruct, meta-llama-3-3-70b-instruct,
                meta-llama-4-scout-17b, meta-llama-4-maverick-17b
        Qwen:   qwen3-coder-480b, qwen3-235b-instruct
        DeepSeek: deepseek-r1, deepseek-v3-1
        Azure:  azure-gpt-4o, azure-gpt-5, azure-gpt-5-mini, azure-gpt-5-2, azure-o4-mini
        OnPrem: onprem-gpt-oss-120b, onprem-llama-3-3-chat, onprem-qwen3-32b 等
    
    别名支持: "sonnet", "opus", "gemini", "llama", "gpt-5", "deepseek" 等
    """
    
    _instance: Optional["LLMSkill"] = None
    _lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None
    
    # 默认配置
    DEFAULT_MODEL = "claude-sonnet-4-5"  # 与 JEDAI 配置一致
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.0
    MAX_RETRIES = 3
    
    def __init__(self):
        """初始化 (私有，请使用 get_instance())"""
        self._client = None
        self._client_type: str = "unknown"
        
        # 统计
        self._global_stats = LLMStats()
        self._agent_stats: Dict[str, LLMStats] = {}
        
        # 初始化客户端
        self._init_client()
    
    @classmethod
    def get_instance(cls) -> "LLMSkill":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置实例 (用于测试)"""
        cls._instance = None
    
    def _init_client(self) -> None:
        """初始化 LLM 客户端 (JEDAI 优先)"""
        # 尝试 JEDAI
        try:
            from ...jedai_client import JedaiClient
            self._client = JedaiClient()
            self._client_type = "JEDAI"
            logger.info("LLMSkill: Using JEDAI client")
            return
        except ImportError:
            pass
        
        # 尝试 Anthropic
        try:
            from anthropic import Anthropic
            self._client = Anthropic()
            self._client_type = "Anthropic"
            logger.info("LLMSkill: Using Anthropic client")
            return
        except ImportError:
            pass
        
        raise ImportError(
            "LLMSkill: 需要 JEDAI 或 Anthropic SDK。\n"
            "JEDAI: 确保 jedai_client.py 可导入\n"
            "Anthropic: pip install anthropic"
        )
    
    @property
    def client_type(self) -> str:
        """当前使用的客户端类型"""
        return self._client_type
    
    # ========================================================================
    # 核心 API
    # ========================================================================
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        agent_id: str = "default",
        model: str = None,
        max_tokens: int = None,
        temperature: float = None,
    ) -> LLMResponse:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system: 系统提示
            agent_id: Agent 标识 (用于分组统计)
            model: 模型名称 (默认 claude-sonnet-4-20250514)
            max_tokens: 最大输出 tokens (默认 4096)
            temperature: 温度 (默认 0.0)
        
        Returns:
            LLMResponse: 响应对象
        
        Raises:
            ConnectionError: 无法连接 LLM 服务
            ValueError: LLM 输出被截断
            Exception: 其他 LLM 错误
        """
        model = model or self.DEFAULT_MODEL
        max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS
        temperature = temperature if temperature is not None else self.DEFAULT_TEMPERATURE
        
        # 初始化 Agent 统计
        if agent_id not in self._agent_stats:
            self._agent_stats[agent_id] = LLMStats()
        
        # 调用 (含重试)
        response = await self._call_with_retry(
            messages=messages,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            agent_id=agent_id,
        )
        
        # 更新统计
        self._update_stats(agent_id, response)
        
        return response
    
    async def _call_with_retry(
        self,
        messages: List[Dict],
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
        agent_id: str,
    ) -> LLMResponse:
        """调用 LLM (含指数退避重试)"""
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=messages,
                )
                
                # 提取响应
                content = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                stop_reason = getattr(response, 'stop_reason', 'end_turn')
                
                # 检查截断
                if stop_reason == "max_tokens":
                    raise ValueError(
                        f"LLM output truncated (max_tokens={max_tokens}). "
                        "Consider increasing max_tokens."
                    )
                
                return LLMResponse(
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    stop_reason=stop_reason,
                    raw_response=response,
                )
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # 检查是否为限流错误
                is_rate_limit = any(
                    x in error_str 
                    for x in ['429', '529', 'rate', 'overloaded', 'capacity']
                )
                
                if is_rate_limit and attempt < self.MAX_RETRIES - 1:
                    # 指数退避 + 随机抖动
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"[LLMSkill] Rate limited, retrying in {wait_time:.1f}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                # 更新错误统计
                self._agent_stats[agent_id].error_count += 1
                self._global_stats.error_count += 1
                
                raise
        
        # 所有重试都失败
        raise last_error
    
    def _update_stats(self, agent_id: str, response: LLMResponse) -> None:
        """更新统计"""
        now = datetime.now().isoformat()
        
        # 全局统计
        self._global_stats.input_tokens += response.input_tokens
        self._global_stats.output_tokens += response.output_tokens
        self._global_stats.call_count += 1
        self._global_stats.last_call_time = now
        
        # Agent 统计
        agent_stats = self._agent_stats[agent_id]
        agent_stats.input_tokens += response.input_tokens
        agent_stats.output_tokens += response.output_tokens
        agent_stats.call_count += 1
        agent_stats.last_call_time = now
    
    # ========================================================================
    # 统计 API
    # ========================================================================
    
    def get_stats(self, agent_id: str = None) -> Dict:
        """
        获取 Token 统计
        
        Args:
            agent_id: Agent 标识，None 返回全局统计
        
        Returns:
            Dict with input_tokens, output_tokens, call_count, error_count
        """
        if agent_id:
            stats = self._agent_stats.get(agent_id, LLMStats())
            return stats.to_dict()
        return self._global_stats.to_dict()
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """获取所有统计 (全局 + 各 Agent)"""
        result = {
            "global": self._global_stats.to_dict(),
            "agents": {
                agent_id: stats.to_dict()
                for agent_id, stats in self._agent_stats.items()
            }
        }
        return result
    
    def reset_stats(self, agent_id: str = None) -> None:
        """
        重置统计
        
        Args:
            agent_id: Agent 标识，None 重置全局统计
        """
        if agent_id:
            if agent_id in self._agent_stats:
                self._agent_stats[agent_id] = LLMStats()
        else:
            self._global_stats = LLMStats()
            self._agent_stats.clear()
    
    # ========================================================================
    # 便捷方法
    # ========================================================================
    
    async def generate_json(
        self,
        prompt: str,
        system: str = "",
        agent_id: str = "default",
        **kwargs
    ) -> Dict:
        """
        生成 JSON 响应
        
        自动解析 JSON，支持 code block 提取
        
        Args:
            prompt: 用户 prompt
            system: 系统提示
            agent_id: Agent 标识
            **kwargs: 传递给 chat() 的其他参数
        
        Returns:
            Dict: 解析后的 JSON
        """
        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            agent_id=agent_id,
            **kwargs
        )
        
        return self._parse_json(response.content)
    
    def _parse_json(self, content: str) -> Dict:
        """解析 JSON (支持 code block)"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取 ```json code block
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                try:
                    return json.loads(content[start:end].strip())
                except json.JSONDecodeError:
                    pass
        
        # 尝试提取 ``` code block
        if "```" in content:
            start = content.find("```") + 3
            # 跳过语言标识行
            newline = content.find("\n", start)
            if newline > start:
                start = newline + 1
            end = content.find("```", start)
            if end > start:
                try:
                    return json.loads(content[start:end].strip())
                except json.JSONDecodeError:
                    pass
        
        raise ValueError(f"Cannot parse JSON from LLM response: {content[:200]}...")


# ============================================================================
# 便捷函数
# ============================================================================

def get_llm_skill() -> LLMSkill:
    """获取 LLMSkill 单例"""
    return LLMSkill.get_instance()


# ============================================================================
# Mock 支持 (用于测试)
# ============================================================================

class MockLLMSkill(LLMSkill):
    """Mock LLM Skill (用于测试)"""
    
    def __init__(self):
        self._client = None
        self._client_type = "Mock"
        self._global_stats = LLMStats()
        self._agent_stats: Dict[str, LLMStats] = {}
        self._mock_responses: List[str] = []
        self._response_index = 0
    
    def _init_client(self) -> None:
        """Mock 不初始化真实客户端"""
        pass
    
    def set_mock_responses(self, responses: List[str]) -> None:
        """设置 Mock 响应"""
        self._mock_responses = responses
        self._response_index = 0
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        agent_id: str = "default",
        **kwargs
    ) -> LLMResponse:
        """返回 Mock 响应"""
        if agent_id not in self._agent_stats:
            self._agent_stats[agent_id] = LLMStats()
        
        # 获取下一个 Mock 响应
        if self._mock_responses:
            content = self._mock_responses[self._response_index % len(self._mock_responses)]
            self._response_index += 1
        else:
            content = '{"mock": "response"}'
        
        # 模拟 token 统计
        input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
        output_tokens = len(content) // 4
        
        response = LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model="mock-model",
            stop_reason="end_turn",
        )
        
        self._update_stats(agent_id, response)
        return response


def set_mock_mode(responses: List[str] = None) -> MockLLMSkill:
    """
    设置 Mock 模式 (用于测试)
    
    Example:
        mock = set_mock_mode(['{"result": "ok"}'])
        response = await get_llm_skill().chat(...)
    """
    mock = MockLLMSkill()
    if responses:
        mock.set_mock_responses(responses)
    LLMSkill._instance = mock
    return mock


# ============================================================================
# CLI 测试
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("LLM Skill Test")
        print("=" * 50)
        
        llm = get_llm_skill()
        print(f"Client type: {llm.client_type}")
        
        # 测试调用
        response = await llm.chat(
            messages=[{"role": "user", "content": "Say 'hello' only."}],
            system="You are a helpful assistant.",
            agent_id="test_agent",
            max_tokens=50
        )
        
        print(f"Response: {response.content}")
        print(f"Tokens: {response.input_tokens} in, {response.output_tokens} out")
        print()
        
        # 打印统计
        print("Stats:")
        print(json.dumps(llm.get_all_stats(), indent=2))
    
    asyncio.run(test())
