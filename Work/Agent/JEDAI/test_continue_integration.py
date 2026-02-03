#!/usr/bin/env python3
"""
测试JEDAI与Continue集成
验证配置是否正确
"""
import requests
import json
from pathlib import Path

JEDAI_URL = "http://sjf-dsgdspr-084.cadence.com:5668"
CHAT_ENDPOINT = f"{JEDAI_URL}/api/copilot/v1/llm/chat/completions"

def load_token():
    """从文件加载Token"""
    token_file = Path("jedai_token.txt")
    if not token_file.exists():
        print("❌ Token文件不存在，请先运行: python get_jedai_token.py")
        return None
    
    with open(token_file, 'r') as f:
        first_line = f.readline()
        token = first_line.replace("Token: ", "").strip()
    return token

def test_model(model_config, token):
    """测试单个模型"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    body = {
        "messages": [
            {"role": "user", "content": "Say hello in one word"}
        ],
        "max_tokens": 50,
        **model_config
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, headers=headers, json=body, timeout=30)
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return True, content
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print("JEDAI Continue集成测试")
    print("=" * 70)
    
    # 加载Token
    print("\n📋 步骤1: 加载认证Token")
    token = load_token()
    if not token:
        return
    print(f"✓ Token已加载 (长度: {len(token)} 字符)")
    
    # 定义测试模型
    test_models = [
        {
            "name": "Gemini 2.5 Pro",
            "config": {
                "model": "GEMINI",
                "deployment": "gemini-2.5-pro",
                "project": "gcp-cdns-llm-test",
                "location": "us-central1"
            }
        },
        {
            "name": "Claude Sonnet 4",
            "config": {
                "model": "Claude",
                "deployment": "claude-sonnet-4",
                "project": "gcp-cdns-llm-test",
                "location": "us-east5",
                "anthropic_version": "vertex-2023-10-16"
            }
        },
        {
            "name": "Llama 3.3",
            "config": {
                "model": "Llama3.3_JEDAI_MODEL_CHAT_2",
                "deployment": "Llama3.3_JEDAI_MODEL_CHAT_2"
            }
        }
    ]
    
    # 测试各个模型
    print("\n🧪 步骤2: 测试模型连接")
    print("-" * 70)
    
    results = []
    for model_info in test_models:
        name = model_info["name"]
        print(f"\n测试 {name}...", end=" ")
        
        success, response = test_model(model_info["config"], token)
        results.append({"name": name, "success": success, "response": response})
        
        if success:
            print(f"✅ 成功")
            print(f"   响应: {response[:50]}...")
        else:
            print(f"❌ 失败")
            print(f"   错误: {response[:100]}")
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['name']}")
    
    print(f"\n通过率: {success_count}/{total_count} ({success_count*100//total_count}%)")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！Continue配置正确。")
        print("\n📋 下一步:")
        print("   1. 重启VSCode")
        print("   2. 打开Continue面板 (Ctrl+L)")
        print("   3. 选择模型开始对话")
    elif success_count > 0:
        print("\n⚠️  部分模型可用，可以继续使用通过测试的模型")
    else:
        print("\n❌ 所有测试失败，请检查:")
        print("   1. Token是否有效 (运行 python get_jedai_token.py)")
        print("   2. 网络连接是否正常")
        print("   3. JEDAI服务器是否可访问")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
