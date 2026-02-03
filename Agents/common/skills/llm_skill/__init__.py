"""
LLM Skill - 统一 LLM 调用入口

提供:
- LLMSkill: 单例模式的 LLM 客户端
- get_llm_skill(): 获取 LLMSkill 实例
"""

from .llm_skill import LLMSkill, get_llm_skill, LLMResponse

__all__ = ["LLMSkill", "get_llm_skill", "LLMResponse"]
