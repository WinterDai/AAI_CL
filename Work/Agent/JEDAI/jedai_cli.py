#!/usr/bin/env python3
"""
JEDAI CLI - Quick access to all JEDAI models from command line
Usage: python jedai_cli.py [model] "your question"
"""
import sys
import json
from jedai_auth import JedaiAuth
from model_config import get_model_config
import httpx

def ask_jedai(model: str, prompt: str, system: str = ""):
    """Ask JEDAI a question"""
    auth = JedaiAuth()
    
    # Get model config
    model_config, real_name = get_model_config(model)
    if not model_config:
        # Fallback: check if 'model' was actually part of the prompt
        # Logic: If user typed 'jedai "some question"' but it got parsed as model="some", prompt="question"
        # We try to rescue it. But here we are in ask_jedai where model is explicit.
        # If explicit model is invalid, we fail.
        print(f"❌ Model '{model}' not found")
        print("\nAvailable models: claude, gpt-4, gemini, deepseek, llama, etc.")
        print("Run 'jedai --list' to see all.")
        return
    
    # Prepare request
    family = model_config["family"]
    deployment = model_config["deployment"]
    print(f"\n🤖 Using: {real_name} ({family} / {deployment})")
    print("━" * 60)
    
    try:
        with httpx.Client(verify=False, timeout=60.0) as client:
            response = client.post(url, json=body, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = result.get("usage", {})
                
                print(content)
                print("\n" + "━" * 60)
                print(f"📊 Tokens: {usage.get('total_tokens', 0)} "
                      f"(prompt: {usage.get('prompt_tokens', 0)}, "
                      f"completion: {usage.get('completion_tokens', 0)})")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

def interactive_mode(model: str, system: str = ""):
    """Run in interactive chat mode"""
    model_config, real_name = get_model_config(model)
    if not model_config:
        print(f"❌ Model '{model}' not found. Using default 'claude'.")
        model = "claude"
        model_config, real_name = get_model_config(model)

    print(f"\n💬 Starting chat with {real_name}")
    print(f"   Family: {model_config['family']} | Deployment: {model_config['deployment']}")
    print("   (Type 'exit', 'quit' or Ctrl+C to stop, 'clear' to reset context)\n")
    print("━" * 60)

    history = []
    if system:
        history.append({"role": "system", "content": system})

    auth = JedaiAuth()
    
    while True:
        try:
            prompt = input("\n👤 You: ").strip()
            if not prompt: continue
            
            if prompt.lower() in ['exit', 'quit']:
                print("\n👋 Goodbye!")
                break
            
            if prompt.lower() == 'clear':
                history = [h for h in history if h['role'] == 'system']
                print("\n🧹 Context cleared.")
                continue

            # Add user message to history
            history.append({"role": "user", "content": prompt})
            
            # Prepare request
            family = model_config["family"]
            deployment = model_config["deployment"]
            location = model_config.get("location", "us-east5")
            endpoint = model_config.get("endpoint")
            
            body = {
                "messages": history,
                "model": family,
                "deployment": deployment,
                "max_tokens": 4096,
                "stream": False
            }
            
            if family == "AzureOpenAI":
                if endpoint:
                    body["endpoint"] = endpoint
                if deployment not in ["gpt-5", "gpt-5-mini", "gpt-5-2"]:
                    body["temperature"] = 0.7
            else:
                body["location"] = location
                body["project"] = "gcp-cdns-llm-test"
                body["temperature"] = 0.7

            # Make request
            token = auth.get_token()
            url = f"{auth.connected_url}/api/copilot/v1/llm/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            print(f"\n🤖 {real_name}: ", end="", flush=True)
            
            with httpx.Client(verify=False, timeout=120.0) as client:
                response = client.post(url, json=body, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    print(content)
                    history.append({"role": "assistant", "content": content})
                else:
                    print(f"\n❌ Error: HTTP {response.status_code}")
                    print(response.text)
                    # Don't add failed user message to history to allow retry
                    history.pop()
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("""
╔══════════════════════════════════════════════════════════════╗
║                      JEDAI CLI Tool                          ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python jedai_cli.py [model] "your question"
  
Examples:
  python jedai_cli.py claude "What is Python?"
  python jedai_cli.py gpt-4 "Explain async/await"
  python jedai_cli.py gemini "Write a quicksort in Python"
  python jedai_cli.py deepseek "Debug this code: ..."

Available models (shortcuts):
  • claude      → Claude 3.7 Sonnet (recommended)
  • gpt-4       → Azure GPT-4o
  • gpt-5       → Azure GPT-5.2
  • gemini      → Gemini 2.5 Pro
  • deepseek    → DeepSeek R1
  • llama       → Llama 3.3 70B
  
Full model names also supported:
  • claude-opus-4-1, claude-3-7-sonnet, claude-haiku-4-5
  • azure-gpt-5-2, azure-gpt-4o, azure-o4-mini
  • gemini-3-pro-preview, gemini-2-5-pro
  • deepseek-r1-0528-maas, deepseek-v3-1-maas
  • llama-4-maverick-17b-128e-instruct-maas
  • qwen3-235b-a22b-instruct-2507-maas
  ...and 30+ more models!

List all models:
  python jedai_cli.py --list
        """)
        sys.exit(0)
    
    if sys.argv[1] == "--list":
        from model_config import JEDAI_MODELS
        print("\n📚 All available JEDAI models:\n")
        for i, (model_id, config) in enumerate(JEDAI_MODELS.items(), 1):
            print(f"{i:2d}. {model_id:40s} - {config['family']} / {config['deployment']}")
        print(f"\nTotal: {len(JEDAI_MODELS)} models")
        sys.exit(0)
    
    # Parse arguments
    if len(sys.argv) == 1:
        # No args -> Interactive mode with default model
        interactive_mode("claude")
    elif len(sys.argv) == 2:
        # One arg -> Interactive mode with specified model
        # OR Single prompt if arg is not a known model/alias (heuristic)
        arg = sys.argv[1]
        
        # Check if arg is likely a model name
        is_model_likely = False
        temp_config, _ = get_model_config(arg)
        if temp_config: 
            is_model_likely = True
        
        if is_model_likely:
            interactive_mode(arg)
        else:
            # Treat as prompt for default model
            ask_jedai("claude", arg)
    else:
        # Two+ args -> One-shot query: python jedai_cli.py [model] "query"
        model = sys.argv[1]
        prompt = " ".join(sys.argv[2:])
        ask_jedai(model, prompt)
