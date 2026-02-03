#!/usr/bin/env python3
"""
JEDAI MCP Server
Exposes JEDAI API as an MCP server for direct use in VS Code Copilot
"""
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, 
    Tool, 
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types
import os

# Import our JEDAI client - use absolute Windows path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from jedai_auth import JedaiAuth
from model_config import JEDAI_MODELS, MODEL_ALIASES, get_model_config
import httpx

# Initialize JEDAI auth
auth = JedaiAuth()

# Create MCP server
app = Server("jedai-mcp")

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available JEDAI models as resources"""
    resources = []
    
    # Add all available models
    for model_id, config in JEDAI_MODELS.items():
        resources.append(Resource(
            uri=f"jedai://model/{model_id}",
            name=f"JEDAI Model: {model_id}",
            mimeType="application/json",
            description=f"{config['family']} - {config['deployment']}"
        ))
    
    return resources

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Get details about a specific model"""
    if uri.startswith("jedai://model/"):
        model_id = uri.replace("jedai://model/", "")
        config = JEDAI_MODELS.get(model_id)
        
        if config:
            return json.dumps({
                "model_id": model_id,
                "family": config["family"],
                "deployment": config["deployment"],
                "location": config.get("location"),
                "endpoint": config.get("endpoint")
            }, indent=2)
    
    return json.dumps({"error": "Model not found"})

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available JEDAI tools"""
    return [
        Tool(
            name="ask_jedai",
            description="Ask a question to any JEDAI model (Claude, GPT-5, Gemini, DeepSeek, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model to use (e.g., 'claude-3-7-sonnet', 'azure-gpt-5-2', 'gemini-2-5-pro')",
                        "default": "claude-3-7-sonnet"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "The question or prompt to send"
                    },
                    "system": {
                        "type": "string",
                        "description": "Optional system message",
                        "default": ""
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "default": 2048
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature (0.0-1.0)",
                        "default": 0.7
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="list_jedai_models",
            description="List all available JEDAI models",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute JEDAI tool calls"""
    
    if name == "list_jedai_models":
        models_info = []
        for model_id, config in JEDAI_MODELS.items():
            models_info.append(f"• {model_id}: {config['family']} - {config['deployment']}")
        
        return [TextContent(
            type="text",
            text="Available JEDAI models:\n\n" + "\n".join(models_info)
        )]
    
    elif name == "ask_jedai":
        model = arguments.get("model", "claude-3-7-sonnet")
        prompt = arguments.get("prompt")
        system = arguments.get("system", "")
        max_tokens = arguments.get("max_tokens", 2048)
        temperature = arguments.get("temperature", 0.7)
        
        # Get model config
        model_config, real_name = get_model_config(model)
        if not model_config:
            return [TextContent(
                type="text",
                text=f"Error: Model '{model}' not found"
            )]
        
        # Prepare request
        family = model_config["family"]
        deployment = model_config["deployment"]
        location = model_config.get("location", "us-east5")
        endpoint = model_config.get("endpoint")
        project = "gcp-cdns-llm-test"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        body = {
            "messages": messages,
            "model": family,
            "deployment": deployment,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if family == "AzureOpenAI":
            if endpoint:
                body["endpoint"] = endpoint
            if deployment not in ["gpt-5", "gpt-5-mini", "gpt-5-2"]:
                body["temperature"] = temperature
        else:
            body["location"] = location
            body["project"] = project
            body["temperature"] = temperature
        
        # Make request
        token = auth.get_token()
        url = f"{auth.connected_url}/api/copilot/v1/llm/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with httpx.AsyncClient(verify=False, timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(url, json=body, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return [TextContent(
                        type="text",
                        text=f"[{model}] {content}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"Error: HTTP {response.status_code}\n{response.text}"
                    )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error calling JEDAI: {str(e)}"
            )]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server"""
    # Ensure we're connected to JEDAI
    if not auth.connect():
        print("Failed to connect to JEDAI", file=sys.stderr)
        sys.exit(1)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
