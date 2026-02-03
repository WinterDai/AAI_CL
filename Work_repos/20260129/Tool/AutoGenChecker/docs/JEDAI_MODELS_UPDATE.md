# JEDAI模型配置完成总结

## 更新内容

已成功将 `jedai_client.py` 更新为使用 `https://jedai-ai:2513/` API，并添加了从API动态发现的所有可用模型。

## 可用模型列表 (共37个)

### Gemini 系列 (4个)
1. **gemini-2-5-pro** - Gemini 2.5 Pro
2. **gemini-2-5-flash** - Gemini 2.5 Flash  
3. **gemini-2-5-flash-lite** - Gemini 2.5 Flash Lite
4. **gemini-1-5-pro** - Gemini 1.5 Pro

### Claude 系列 (8个)
5. **claude-sonnet-4-5** - Claude Sonnet 4.5
6. **claude-sonnet-4** - Claude Sonnet 4
7. **claude-haiku-4-5** - Claude Haiku 4.5
8. **claude-opus-4-1** - Claude Opus 4.1
9. **claude-opus-4** - Claude Opus 4
10. **claude-3-7-sonnet** - Claude 3.7 Sonnet
11. **claude-3-5-sonnet** - Claude 3.5 Sonnet
12. **claude-3-opus** - Claude 3 Opus

### Meta Llama 系列 (6个)
13. **meta-llama-3-1-8b-instruct** - Meta Llama 3.1 8B Instruct
14. **meta-llama-3-1-70b-instruct** - Meta Llama 3.1 70B Instruct
15. **meta-llama-3-1-405b-instruct** - Meta Llama 3.1 405B Instruct
16. **meta-llama-3-3-70b-instruct** - Meta Llama 3.3 70B Instruct
17. **meta-llama-4-scout-17b** - Meta Llama 4 Scout 17B
18. **meta-llama-4-maverick-17b** - Meta Llama 4 Maverick 17B

### Qwen 系列 (2个)
19. **qwen3-coder-480b** - Qwen3 Coder 480B (专为编程优化)
20. **qwen3-235b-instruct** - Qwen3 235B Instruct

### DeepSeek 系列 (2个)
21. **deepseek-r1** - DeepSeek R1 (推理模型)
22. **deepseek-v3-1** - DeepSeek V3.1

### Azure OpenAI 系列 (7个)
23. **azure-gpt-4o** - Azure GPT-4o
24. **azure-o4-mini** - Azure o4-mini (推理模型)
25. **azure-gpt-5** - Azure GPT-5
26. **azure-gpt-5-mini** - Azure GPT-5 Mini
27. **azure-gpt-5-2** - Azure GPT-5.2
28. **azure-gpt-4-vision** - Azure GPT-4 Vision
29. **azure-gpt-4-turbo** - Azure GPT-4 Turbo

### On-Premise 系列 (8个)
30. **onprem-gpt-oss-120b** - On-Prem GPT OSS 120B
31. **onprem-gpt-oss-120b-sj** - On-Prem GPT OSS 120B (SJ)
32. **onprem-gpt-oss-20b** - On-Prem GPT OSS 20B
33. **onprem-gpt-oss-70b** - On-Prem GPT OSS 70B
34. **onprem-llama-3-1-chat** - On-Prem Llama 3.1 Chat
35. **onprem-llama-3-3-chat** - On-Prem Llama 3.3 Chat
36. **onprem-qwen3-32b** - On-Prem Qwen3 32B
37. **onprem-llama-3-3-nemotron-49b** - On-Prem Llama 3.3 Nemotron 49B

## 便捷别名

```python
# 可以使用简短的别名来调用模型
"gemini"     → gemini-2-5-pro
"gemini-flash" → gemini-2-5-flash
"claude"     → claude-opus-4
"opus"       → claude-opus-4
"sonnet"     → claude-sonnet-4
"haiku"      → claude-haiku-4-5
"llama"      → meta-llama-3-3-70b-instruct
"llama-3"    → meta-llama-3-3-70b-instruct
"llama-4"    → meta-llama-4-scout-17b
"qwen"       → qwen3-coder-480b
"deepseek"   → deepseek-v3-1
"deepseek-r1" → deepseek-r1
"gpt-4o"     → azure-gpt-4o
"gpt-5"      → azure-gpt-5
"gpt-5-mini" → azure-gpt-5-mini
"gpt-5-2"    → azure-gpt-5-2
"o4-mini"    → azure-o4-mini
"onprem-gpt" → onprem-gpt-oss-120b
"onprem-llama" → onprem-llama-3-3-chat
```

## 使用示例

```python
from llm_clients.jedai_client import JedAIClient

# 方式1: 使用完整模型名
client = JedAIClient(default_model="claude-sonnet-4-5")

# 方式2: 使用别名
client = JedAIClient(default_model="sonnet")

# 方式3: 使用新的Llama模型
client = JedAIClient(default_model="meta-llama-4-scout-17b")

# 方式4: 使用Qwen编程模型
client = JedAIClient(default_model="qwen3-coder-480b")

# 发送请求
response = client.complete("你的问题")
print(response.text)
```

## 模型推荐

### 云端模型（GCP/Azure）
- **编程任务**: `qwen3-coder-480b` (专为代码设计) 或 `azure-gpt-5-2`
- **复杂推理**: `claude-opus-4-1`, `claude-sonnet-4-5`, `deepseek-r1` 或 `azure-gpt-5`
- **推理专用**: `azure-o4-mini` (OpenAI o系列) 或 `deepseek-r1`
- **快速响应**: `claude-haiku-4-5` 或 `gemini-2-5-flash-lite`
- **平衡性能**: `claude-sonnet-4`, `gemini-2-5-pro`, `deepseek-v3-1` 或 `azure-gpt-4o`
- **视觉任务**: `azure-gpt-4-vision` (支持图像输入)
- **开源替代**: `meta-llama-3-3-70b-instruct` 或 `meta-llama-4-scout-17b`

### 本地部署模型（On-Premise）
- **大规模任务**: `onprem-gpt-oss-120b` (最大容量)
- **平衡选择**: `onprem-gpt-oss-70b`
- **轻量快速**: `onprem-gpt-oss-20b`
- **对话任务**: `onprem-llama-3-3-chat` 或 `onprem-llama-3-3-nemotron-49b`
- **编程任务**: `onprem-qwen3-32b`

## 工具脚本

1. **discover_jedai_models.py** - 查询API获取所有可用模型
2. **generate_model_config.py** - 生成Python配置代码
3. **test_jedai_models.py** - 测试模型连通性

## 注意事项

- API地址已更新为: `https://jedai-ai:2513`
- 所有模型使用LDAP认证（Cadence内部凭据）
- SSL验证已禁用以支持内部服务器
- 自动故障转移到备用URL
