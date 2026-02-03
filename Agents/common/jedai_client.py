"""
JEDAI LLM Client

通过 JEDAI 代理层访问 Claude 模型

配置方式:
1. 环境变量 (推荐):
   - JEDAI_USERNAME: 用户名
   - JEDAI_PASSWORD: 密码
   - JEDAI_URL: JEDAI 服务地址 (可选, 默认 https://jedai-ai:2513)
   - JEDAI_TOKEN: 直接提供 token (可选，跳过认证)

2. 代码配置:
   client = JedaiClient(username="xxx", password="xxx")
   
3. Token 缓存:
   - 首次认证后自动保存到 ~/.jedai_token
   - 下次启动自动加载，无需重新输入密码
   - Token 过期后自动重新认证
"""

import os
import json
import getpass
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# JEDAI 默认配置
JEDAI_URLS = [
    "https://jedai-ai:2513",           # 主 URL (推荐)
    "http://jedai-ai.cadence.com:5668", # 备用 URL
]

DEFAULT_DEPLOYMENT = "claude-sonnet-4-5"

# Token 缓存文件
TOKEN_CACHE_FILE = Path.home() / ".jedai_token"

# JEDAI 支持的模型配置 (从 AutoGenChecker 同步 - 37 models total)
JEDAI_MODELS = {
    # ========== GEMINI models ==========
    "gemini-2-5-pro": {"family": "GEMINI", "location": "us-central1", "deployment": "gemini-2.5-pro"},
    "gemini-2-5-flash": {"family": "GEMINI", "location": "us-central1", "deployment": "gemini-2.5-flash"},
    "gemini-2-5-flash-lite": {"family": "GEMINI", "location": "us-central1", "deployment": "gemini-2.5-flash-lite"},
    "gemini-1-5-pro": {"family": "GEMINI", "location": "us-central1", "deployment": "gemini-1.5-pro"},
    "gemini-3-pro-preview": {"family": "GEMINI", "location": "us-central1", "deployment": "gemini-3-pro-preview"},  # 新模型
    
    # ========== Claude models ==========
    "claude-sonnet-4-5": {"family": "Claude", "location": "us-east5", "deployment": "claude-sonnet-4-5"},
    "claude-sonnet-4": {"family": "Claude", "location": "us-east5", "deployment": "claude-sonnet-4"},
    "claude-haiku-4-5": {"family": "Claude", "location": "us-east5", "deployment": "claude-haiku-4-5"},
    "claude-opus-4-1": {"family": "Claude", "location": "us-east5", "deployment": "claude-opus-4-1"},
    "claude-opus-4": {"family": "Claude", "location": "us-east5", "deployment": "claude-opus-4"},
    "claude-3-7-sonnet": {"family": "Claude", "location": "us-east5", "deployment": "claude-3-7-sonnet"},
    "claude-3-5-sonnet": {"family": "Claude", "location": "us-east5", "deployment": "claude-3-5-sonnet"},
    "claude-3-opus": {"family": "Claude", "location": "us-east5", "deployment": "claude-3-opus"},
    
    # ========== Meta-Llama models ==========
    "meta-llama-3-1-8b-instruct": {"family": "Meta-Llama", "location": "us-central1", "deployment": "meta/llama-3.1-8b-instruct-maas"},
    "meta-llama-3-1-70b-instruct": {"family": "Meta-Llama", "location": "us-central1", "deployment": "meta/llama-3.1-70b-instruct-maas"},
    "meta-llama-3-1-405b-instruct": {"family": "Meta-Llama", "location": "us-central1", "deployment": "meta/llama-3.1-405b-instruct-maas"},
    "meta-llama-3-3-70b-instruct": {"family": "Meta-Llama", "location": "us-central1", "deployment": "meta/llama-3.3-70b-instruct-maas"},
    "meta-llama-4-scout-17b": {"family": "Meta-Llama", "location": "us-east5", "deployment": "meta/llama-4-scout-17b-16e-instruct-maas"},
    "meta-llama-4-maverick-17b": {"family": "Meta-Llama", "location": "us-east5", "deployment": "meta/llama-4-maverick-17b-128e-instruct-maas"},
    
    # ========== Qwen models ==========
    "qwen3-coder-480b": {"family": "Qwen", "location": "us-south1", "deployment": "qwen/qwen3-coder-480b-a35b-instruct-maas"},
    "qwen3-235b-instruct": {"family": "Qwen", "location": "us-south1", "deployment": "qwen/qwen3-235b-a22b-instruct-2507-maas"},
    
    # ========== DeepSeek models ==========
    "deepseek-r1": {"family": "DeepSeek", "location": "us-central1", "deployment": "deepseek-ai/deepseek-r1-0528-maas"},
    "deepseek-v3-1": {"family": "DeepSeek", "location": "us-central1", "deployment": "deepseek-ai/deepseek-v3.1-maas"},
    
    # ========== Azure OpenAI models ==========
    "azure-gpt-4o": {"family": "AzureOpenAI", "location": "eastus2", "deployment": "gpt-4o", "endpoint": "https://llmtest01-eastus2.openai.azure.com"},
    "azure-o4-mini": {"family": "AzureOpenAI", "location": "eastus2", "deployment": "o4-mini", "endpoint": "https://llmtest01-eastus2.openai.azure.com"},
    "azure-gpt-5": {"family": "AzureOpenAI", "location": "eastus2", "deployment": "gpt-5", "endpoint": "https://llmtest01-eastus2.openai.azure.com"},
    "azure-gpt-5-mini": {"family": "AzureOpenAI", "location": "eastus2", "deployment": "gpt-5-mini", "endpoint": "https://llmtest01-eastus2.openai.azure.com"},
    "azure-gpt-5-2": {"family": "AzureOpenAI", "location": "eastus2", "deployment": "gpt-5-2", "endpoint": "https://llmtest01-eastus2.openai.azure.com"},
    "azure-gpt-4-vision": {"family": "AzureOpenAI", "location": "westus", "deployment": "rnd01-gpt4-vision", "endpoint": "https://llmtest01-westus.openai.azure.com"},
    "azure-gpt-4-turbo": {"family": "AzureOpenAI", "location": "eastus2", "deployment": "gpt-4-turbo", "endpoint": "https://llmtest01-eastus2.openai.azure.com"},
    
    # ========== OnPremise models ==========
    "onprem-gpt-oss-120b": {"family": "OnPremise", "location": "local", "deployment": "on_prem_openai/gpt-oss-120b"},
    "onprem-gpt-oss-120b-sj": {"family": "OnPremise", "location": "local", "deployment": "on_prem_sj_openai/gpt-oss-120b"},
    "onprem-gpt-oss-20b": {"family": "OnPremise", "location": "local", "deployment": "on_prem_openai/gpt-oss-20b"},
    "onprem-llama-3-1-chat": {"family": "OnPremise", "location": "local", "deployment": "on_prem_llama3.1_JEDAI_MODEL_CHAT_2"},
    "onprem-llama-3-3-chat": {"family": "OnPremise", "location": "local", "deployment": "on_prem_llama3.3_JEDAI_MODEL_CHAT_2"},
    "onprem-qwen3-32b": {"family": "OnPremise", "location": "local", "deployment": "on_prem_Qwen3-32B"},
    "onprem-llama-3-3-nemotron-49b": {"family": "OnPremise", "location": "local", "deployment": "on_prem_nvidia/llama-3_3-nemotron-super-49b-v1_5"},
    "onprem-gpt-oss-70b": {"family": "OnPremise", "location": "local", "deployment": "on_prem_openai/gpt-oss-70b"},
}

# 模型别名 (便捷使用)
MODEL_ALIASES = {
    # Gemini
    "gemini": "gemini-2-5-pro",
    "gemini-pro": "gemini-2-5-pro",
    "gemini-flash": "gemini-2-5-flash",
    "gemini-3-0-pro-preview": "gemini-3-0-pro-preview",  # 新模型 (如果 JEDAI 支持)
    # Claude
    "claude": "claude-opus-4",
    "opus": "claude-opus-4",
    "sonnet": "claude-sonnet-4-5",
    "haiku": "claude-haiku-4-5",
    "claude-sonnet-4-20250514": "claude-sonnet-4",  # Anthropic SDK 格式别名
    # Llama
    "llama": "meta-llama-3-3-70b-instruct",
    "llama-3": "meta-llama-3-3-70b-instruct",
    "llama-4": "meta-llama-4-scout-17b",
    # Qwen
    "qwen": "qwen3-coder-480b",
    # DeepSeek
    "deepseek": "deepseek-v3-1",
    # Azure OpenAI
    "gpt-4o": "azure-gpt-4o",
    "gpt-5": "azure-gpt-5",
    "gpt-5-mini": "azure-gpt-5-mini",
    "gpt-5-2": "azure-gpt-5-2",  # GPT 5.2 别名
    "gpt-5.2": "azure-gpt-5-2",  # GPT 5.2 别名
    "o4-mini": "azure-o4-mini",
    # On-Premise
    "onprem": "onprem-gpt-oss-120b",
    "onprem-gpt": "onprem-gpt-oss-120b",
}


@dataclass
class JedaiResponse:
    """JEDAI 响应"""
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    raw_response: dict


class JedaiClient:
    """
    JEDAI LLM 客户端
    
    兼容 Anthropic SDK 接口，便于替换
    
    Token 缓存:
    - 首次认证后自动保存到 ~/.jedai_token
    - 下次启动自动加载
    - Token 过期后自动重新认证
    """
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        url: Optional[str] = None,
        deployment: str = DEFAULT_DEPLOYMENT,
        cache_token: bool = True  # 是否缓存 token
    ):
        if not HAS_REQUESTS:
            raise ImportError("requests 未安装，请运行: pip install requests")
        
        self.username = username or os.environ.get("JEDAI_USERNAME") or os.environ.get("USER") or os.environ.get("USERNAME")
        self.password = password or os.environ.get("JEDAI_PASSWORD")
        self.url = url or os.environ.get("JEDAI_URL")
        self.deployment = deployment
        self.cache_token = cache_token
        
        self.token: Optional[str] = None
        self._connected_url: Optional[str] = None
        
        # 尝试从环境变量或缓存加载 token
        self._load_cached_token()
    
    def _load_cached_token(self) -> None:
        """从环境变量或缓存文件加载 token"""
        # 优先从环境变量
        env_token = os.environ.get("JEDAI_TOKEN")
        if env_token:
            self.token = env_token
            self._connected_url = self.url or JEDAI_URLS[0]
            return
        
        # 从缓存文件加载
        if TOKEN_CACHE_FILE.exists():
            try:
                with open(TOKEN_CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    self.token = cache.get("token")
                    self._connected_url = cache.get("url")
                    # 检查用户名是否匹配
                    if cache.get("username") != self.username:
                        self.token = None
                        self._connected_url = None
            except Exception:
                pass
    
    def _save_token_cache(self) -> None:
        """保存 token 到缓存文件"""
        if not self.cache_token or not self.token:
            return
        
        try:
            with open(TOKEN_CACHE_FILE, 'w') as f:
                json.dump({
                    "username": self.username,
                    "token": self.token,
                    "url": self._connected_url
                }, f)
            # 设置文件权限为仅用户可读写
            TOKEN_CACHE_FILE.chmod(0o600)
        except Exception:
            pass
    
    def _clear_token_cache(self) -> None:
        """清除 token 缓存"""
        self.token = None
        self._connected_url = None
        if TOKEN_CACHE_FILE.exists():
            try:
                TOKEN_CACHE_FILE.unlink()
            except Exception:
                pass
    
    def _get_password(self) -> str:
        """获取密码（交互式）"""
        if not self.password:
            self.password = getpass.getpass(f"JEDAI Password for {self.username}: ")
        return self.password
    
    def _connect(self, force_reauth: bool = False) -> bool:
        """连接 JEDAI 并认证"""
        # 如果已有 token 且不强制重新认证，直接返回
        if self.token and self._connected_url and not force_reauth:
            return True
        
        urls = [self.url] if self.url else JEDAI_URLS
        password = self._get_password()
        
        for url in urls:
            try:
                response = requests.post(
                    f"{url}/api/v1/security/login",
                    headers={"Content-Type": "application/json"},
                    json={
                        "username": self.username,
                        "password": password,
                        "provider": "LDAP",
                    },
                    timeout=15,
                    verify=False,
                )
                
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    self._connected_url = url
                    # 保存 token 到缓存
                    self._save_token_cache()
                    return True
            except Exception:
                continue
        
        return False
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        model: Optional[str] = None
    ) -> JedaiResponse:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system: 系统提示
            max_tokens: 最大输出 tokens
            temperature: 温度
            model: 模型名称或别名 (可选，支持 37 种模型)
                   别名示例: "sonnet", "opus", "gemini", "llama", "gpt-5" 等
            
        Returns:
            JedaiResponse: 响应对象
        """
        if not self._connect():
            raise ConnectionError("无法连接 JEDAI 服务")
        
        # 解析模型配置 (支持别名)
        model_key = model or self.deployment
        # 先检查别名
        if model_key in MODEL_ALIASES:
            model_key = MODEL_ALIASES[model_key]
        
        model_config = JEDAI_MODELS.get(model_key)
        
        if model_config:
            family = model_config["family"]
            location = model_config["location"]
            deployment = model_config["deployment"]
        else:
            # 未知模型，使用默认配置
            family = "Claude"
            location = "us-east5"
            deployment = model_key
        
        # 构建消息
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)
        
        # 构建请求体 - 根据模型家族调整参数
        body = {
            "messages": all_messages,
            "model": family,
            "deployment": deployment,
            "max_tokens": max_tokens,
        }
        
        # Azure OpenAI 使用 endpoint 参数，不使用 location
        # 注意：某些 Azure 模型（如 GPT-5.2）不支持 temperature 参数
        if family == "AzureOpenAI":
            endpoint = model_config.get("endpoint") if model_config else None
            if endpoint:
                body["endpoint"] = endpoint
            # GPT-5 系列和某些模型不支持自定义 temperature，跳过该参数
            # 其他 Azure 模型可以设置 temperature
            if deployment not in ["gpt-5", "gpt-5-mini", "gpt-5-2"]:
                body["temperature"] = temperature
            # 打印实际调用的 LLM 模型信息
            print(f"[JEDAI] Using LLM: {family}/{deployment} (endpoint: {endpoint})")
        else:
            # 其他模型 (GCP) 使用 location 和 project
            body["location"] = location
            body["project"] = "gcp-cdns-llm-test"
            body["temperature"] = temperature
            # 打印实际调用的 LLM 模型信息
            print(f"[JEDAI] Using LLM: {family}/{deployment} (location: {location})")
        
        # 发送请求，支持 token 过期自动重试
        for attempt in range(2):
            response = requests.post(
                f"{self._connected_url}/api/copilot/v1/llm/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",
                },
                json=body,
                timeout=300,  # 增加到 5 分钟，Layer 2 生成复杂内容需要更长时间
                verify=False,
            )
            
            # 401/403 表示 token 过期，重新认证
            if response.status_code in [401, 403] and attempt == 0:
                self._clear_token_cache()
                if self._connect(force_reauth=True):
                    continue
            
            break
        
        if response.status_code != 200:
            raise Exception(f"JEDAI 请求失败: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # 提取响应
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        
        return JedaiResponse(
            content=content,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            model=result.get("model", self.deployment),
            raw_response=result
        )
    
    # Anthropic SDK 兼容接口
    class Messages:
        def __init__(self, client: "JedaiClient"):
            self.client = client
        
        def create(
            self,
            model: str,
            max_tokens: int,
            temperature: float,
            system: str,
            messages: List[Dict]
        ):
            """兼容 Anthropic SDK 的 messages.create 接口"""
            response = self.client.chat(
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model  # 传递 model 参数
            )
            
            # 返回兼容 Anthropic 的响应结构
            return _AnthropicCompatResponse(response)
    
    @property
    def messages(self):
        return self.Messages(self)


class _AnthropicCompatResponse:
    """Anthropic SDK 兼容响应"""
    
    def __init__(self, jedai_response: JedaiResponse):
        self._response = jedai_response
        
        # 兼容 Anthropic 的 content 结构
        self.content = [_ContentBlock(jedai_response.content)]
        
        # 兼容 Anthropic 的 usage 结构
        self.usage = _Usage(
            jedai_response.input_tokens,
            jedai_response.output_tokens
        )
        
        # 兼容 Anthropic 的 stop_reason (JEDAI 不返回此字段，默认 end_turn)
        self.stop_reason = "end_turn"


class _ContentBlock:
    def __init__(self, text: str):
        self.text = text
        self.type = "text"


class _Usage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


# ============================================================================
# 便捷函数
# ============================================================================

def create_client(
    username: Optional[str] = None,
    password: Optional[str] = None
) -> JedaiClient:
    """
    创建 JEDAI 客户端
    
    Example:
        client = create_client()
        response = client.chat([{"role": "user", "content": "Hello"}])
        print(response.content)
    """
    return JedaiClient(username=username, password=password)


if __name__ == "__main__":
    # 测试
    print("JEDAI Client Test")
    print("="*50)
    
    client = create_client()
    
    response = client.chat(
        messages=[{"role": "user", "content": "Say 'hello' only."}],
        max_tokens=50
    )
    
    print(f"Response: {response.content}")
    print(f"Tokens: {response.input_tokens} in, {response.output_tokens} out")
