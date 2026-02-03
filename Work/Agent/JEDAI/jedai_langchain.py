"""
JEDAI LangChain Integration Module

为JEDAI系统提供LangChain集成支持，支持结构化输出
"""
import sys
from pathlib import Path
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from jedai_auth import JedaiAuth
from model_config import get_model_config

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: langchain not installed. Run: pip install langchain-openai")


T = TypeVar('T', bound=BaseModel)


class JedaiLangChain:
    """
    JEDAI LangChain集成类
    
    功能：
    1. 自动认证和token管理
    2. 支持所有37个JEDAI模型
    3. 自动处理Claude/GCP_OSS的特殊情况
    4. 结构化输出支持
    
    示例：
        >>> jedai = JedaiLangChain()
        >>> llm = jedai.create_llm("claude-3-7-sonnet")
        >>> result = llm.invoke("What is AI?")
        
        # 结构化输出
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>> llm_structured = jedai.create_structured_llm("gpt-4o", Person)
        >>> result = llm_structured.invoke("Alice is 30 years old")
    """
    
    # 需要特殊处理的模型（不支持直接结构化输出）
    SPECIAL_MODELS = {
        'claude', 'claude-3-7-sonnet', 'claude-sonnet-4',
        'gcp-oss', 'gcp_oss', 'gpt-oss-120b'
    }
    
    def __init__(self):
        """初始化JEDAI LangChain集成"""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain not installed. Install with:\n"
                "pip install langchain-openai langchain-core"
            )
        
        self.auth = JedaiAuth()
        print(f"[OK] Connected to JEDAI: {self.auth.connected_url}")
    
    def create_llm(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> ChatOpenAI:
        """
        创建LangChain ChatOpenAI实例
        
        Args:
            model: 模型名称或别名（如 "claude", "gpt-4", "gemini"）
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他ChatOpenAI参数
            
        Returns:
            ChatOpenAI实例
        """
        # 解析模型配置（支持别名）
        model_config, real_name = get_model_config(model)
        
        if not model_config:
            print(f"Warning: Unknown model '{model}', using as-is")
            real_name = model
            model_config = {"family": model, "deployment": model}
        
        # 创建 httpx 客户端以禁用 SSL 验证
        import httpx
        http_client = httpx.Client(verify=False)
        
        # 获取有效的token（自动刷新过期token）
        valid_token = self.auth.get_valid_token()
        
        # 准备模型配置参数
        family = model_config["family"]
        deployment = model_config["deployment"]
        location = model_config.get("location", "us-east5")
        endpoint = model_config.get("endpoint")
        
        # 构建JEDAI模型名称格式: {Family}_{deployment}
        # 例如: GCP_claude-sonnet-4-5, AzureOpenAI_gpt-4o
        if family == "AzureOpenAI":
            jedai_model_name = f"AzureOpenAI_{deployment}"
        elif family in ["Claude", "GEMINI", "DeepSeek", "Meta-Llama", "Qwen"]:
            jedai_model_name = f"GCP_{deployment}"
        elif family == "OnPremise":
            jedai_model_name = f"on_prem_{deployment}"
        elif family == "OpenAI":
            jedai_model_name = "OpenAI"
        else:
            jedai_model_name = f"{family}_{deployment}"
        
        # 打印当前使用的LLM信息
        print(f"[LLM] Using model: {jedai_model_name} (family={family}, deployment={deployment})")
        
        # 构建extra_body用于JEDAI特定参数
        extra_body = {
            "deployment": deployment,
        }
        
        if family == "AzureOpenAI":
            if endpoint:
                extra_body["endpoint"] = endpoint
        else:
            extra_body["location"] = location
            extra_body["project"] = "gcp-cdns-llm-test"
        
        # 创建LangChain ChatOpenAI with correct JEDAI model name
        llm = ChatOpenAI(
            openai_api_base=f"{self.auth.connected_url}/api/copilot/v1/llm",
            openai_api_key=valid_token,
            model_name=jedai_model_name,  # 使用完整的JEDAI格式
            temperature=temperature,
            max_tokens=max_tokens,
            http_client=http_client,
            extra_body=extra_body,  # 使用extra_body传递JEDAI参数
            **kwargs
        )
        
        return llm
    
    def create_structured_llm(
        self,
        model: str,
        schema: Type[T],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        """
        创建支持结构化输出的LLM
        
        自动处理Claude/GCP_OSS等特殊模型
        
        Args:
            model: 模型名称
            schema: Pydantic BaseModel类定义输出结构
            temperature: 温度
            max_tokens: 最大token数
            
        Returns:
            结构化输出LLM（直接调用或链式调用）
            
        示例：
            >>> class Person(BaseModel):
            ...     name: str
            ...     age: int
            >>> 
            >>> jedai = JedaiLangChain()
            >>> llm = jedai.create_structured_llm("gpt-4o", Person)
            >>> result = llm.invoke("Alice is 30")  # 返回Person对象
        """
        llm = self.create_llm(model, temperature, max_tokens, **kwargs)
        
        # 检查是否需要特殊处理
        model_lower = model.lower()
        needs_workaround = any(
            special in model_lower 
            for special in self.SPECIAL_MODELS
        )
        
        if needs_workaround:
            # Claude/GCP_OSS：使用ChatPromptTemplate
            return self._create_claude_structured_llm(llm, schema)
        else:
            # 其他模型：直接使用with_structured_output
            return llm.with_structured_output(schema)
    
    def _create_claude_structured_llm(
        self,
        llm: ChatOpenAI,
        schema: Type[T]
    ):
        """
        为Claude创建结构化输出链
        
        使用ChatPromptTemplate约束输出格式
        """
        llm_with_structure = llm.with_structured_output(schema)
        
        # 创建prompt模板
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a helpful assistant that extracts structured information.
Your task is to extract information from text and return it as a JSON object.
The JSON must conform to the following schema:
{schema}

IMPORTANT: Return ONLY valid JSON without any markdown formatting or code blocks.
Do not include ```json or ``` in your response.
"""
            ),
            ("human", "{text_input}")
        ])
        
        # 创建链
        def invoke_chain(text_input: str) -> T:
            """执行链式调用"""
            return (prompt | llm_with_structure).invoke({
                "schema": schema.model_json_schema(),
                "text_input": text_input
            })
        
        # 返回可调用对象
        class StructuredChain:
            def __init__(self, chain_fn):
                self._chain_fn = chain_fn
            
            def invoke(self, text_input: str) -> T:
                return self._chain_fn(text_input)
        
        return StructuredChain(invoke_chain)
    
    def list_models(self) -> Dict[str, Any]:
        """
        列出所有支持的模型及其结构化输出支持状态
        
        Returns:
            模型配置字典
        """
        from model_config import JEDAI_MODELS, MODEL_ALIASES
        
        print("\n=== JEDAI Models ===\n")
        
        for model_id, config in JEDAI_MODELS.items():
            family = config.get('family', 'Unknown')
            deployment = config.get('deployment', model_id)
            
            # 判断结构化输出支持
            needs_workaround = any(
                special in model_id.lower() 
                for special in self.SPECIAL_MODELS
            )
            support = "⚠️ Workaround" if needs_workaround else "✅ Native"
            
            print(f"{model_id:45} | {family:15} | {support}")
        
        print(f"\n总计: {len(JEDAI_MODELS)} 个模型")
        print(f"别名: {len(MODEL_ALIASES)} 个")
        
        return JEDAI_MODELS


# ============================================================================
# 便捷函数
# ============================================================================

def create_jedai_llm(model: str = "claude", **kwargs) -> ChatOpenAI:
    """
    快速创建JEDAI LLM
    
    示例：
        >>> llm = create_jedai_llm("gpt-4")
        >>> result = llm.invoke("Hello!")
    """
    jedai = JedaiLangChain()
    return jedai.create_llm(model, **kwargs)


def create_structured_jedai_llm(model: str, schema: Type[T], **kwargs):
    """
    快速创建结构化输出LLM
    
    示例：
        >>> class Person(BaseModel):
        ...     name: str
        ...     age: int
        >>> llm = create_structured_jedai_llm("gpt-4", Person)
        >>> result = llm.invoke("Alice is 30")
    """
    jedai = JedaiLangChain()
    return jedai.create_structured_llm(model, schema, **kwargs)


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    print("JEDAI LangChain Integration Test")
    print("=" * 50)
    
    # 测试1: 基础LLM
    print("\n[Test 1] Basic LLM")
    jedai = JedaiLangChain()
    llm = jedai.create_llm("claude")
    response = llm.invoke("Say 'Hello from JEDAI!' only.")
    print(f"Response: {response.content}")
    
    # 测试2: 结构化输出（GPT）
    print("\n[Test 2] Structured Output (GPT-4)")
    
    class Person(BaseModel):
        """A person's information"""
        name: str
        age: int
    
    llm_structured = jedai.create_structured_llm("gpt-4", Person)
    result = llm_structured.invoke("My friend Bob is 25 years old")
    print(f"Name: {result.name}, Age: {result.age}")
    
    # 测试3: 结构化输出（Claude with workaround）
    print("\n[Test 3] Structured Output (Claude with workaround)")
    llm_claude = jedai.create_structured_llm("claude", Person)
    result = llm_claude.invoke("Alice is 30 years old and works as an engineer")
    print(f"Name: {result.name}, Age: {result.age}")
    
    print("\n" + "=" * 50)
    print("✓ All tests passed!")
