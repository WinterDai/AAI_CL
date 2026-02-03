import httpx
import json
import time
import asyncio
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from jedai_auth import JedaiAuth
from model_config import JEDAI_MODELS, get_model_config, MODEL_ALIASES

app = FastAPI(title="JEDAI to OpenAI Proxy")
auth = JedaiAuth()

@app.middleware("http")
async def store_request(request: Request, call_next):
    # Log incoming requests for debugging
    print(f"[REQUEST] {request.method} {request.url.path}")
    print(f"[HEADERS] {dict(request.headers)}")
    
    # Log request body for POST requests
    if request.method == "POST":
        body = await request.body()
        try:
            body_json = json.loads(body)
            print(f"[BODY] Model: {body_json.get('model', 'N/A')}")
            print(f"[BODY] Messages count: {len(body_json.get('messages', []))}")
            print(f"[BODY] Stream: {body_json.get('stream', False)}")
            print(f"[BODY] Keys: {list(body_json.keys())}")
            # Save full body to file for inspection
            with open('last_request.json', 'w') as f:
                json.dump(body_json, f, indent=2)
        except:
            pass
        # Reset body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    # Normalize path to fix double slashes
    if "//" in request.url.path:
        original_path = request.scope["path"]
        request.scope["path"] = original_path.replace("//", "/")
        print(f"[PATH_FIX] {original_path} -> {request.scope['path']}")
    
    response = await call_next(request)
    print(f"[RESPONSE] Status: {response.status_code}")
    return response

# Pydantic models for OpenAI request
class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]] # Allow list for multi-modal
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: Optional[List[ChatMessage]] = None  # Optional for Continue format
    input: Optional[List[Dict[str, Any]]] = None  # Continue format
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None  # Continue uses this
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None  # Continue reasoning field
    include: Optional[List[str]] = None  # Continue include field

    class Config:
        extra = "ignore" # Ignore unknown fields from Continue
    
    def normalize_messages(self) -> List[ChatMessage]:
        """Convert Continue's 'input' format to standard 'messages' format"""
        if self.messages:
            return self.messages
        
        if self.input:
            normalized = []
            for item in self.input:
                if item.get("type") == "message":
                    # Extract role and content from Continue format
                    role = item.get("role", "user")
                    content = item.get("content", "")
                    normalized.append(ChatMessage(role=role, content=content))
            return normalized
        
        return []

@app.on_event("startup")
async def startup_event():
    print("Starting JEDAI Proxy...")
    # Pre-login on startup
    if not auth.connect():
        print("Warning: Initial login failed. Will retry on first request.")

async def build_jedai_body(request: ChatCompletionRequest):
    model_config, real_name = get_model_config(request.model)
    
    # Default fallback if unknown model
    family = "Claude"
    deployment = real_name
    location = "us-east5"
    project = "gcp-cdns-llm-test"
    endpoint = None

    if model_config:
        family = model_config.get("family", "Claude")
        deployment = model_config.get("deployment", real_name)
        location = model_config.get("location", "us-east5")
        endpoint = model_config.get("endpoint")
        # Reuse existing project default
        project = "gcp-cdns-llm-test"

    # Normalize messages (handles both OpenAI and Continue formats)
    normalized_messages = request.normalize_messages()
    
    # Use max_output_tokens if max_tokens not set (Continue compatibility)
    max_tokens = request.max_tokens or request.max_output_tokens or 2048

    body = {
        "messages": [m.dict(exclude_none=True) for m in normalized_messages],
        "model": family,
        "deployment": deployment,
        "max_tokens": max_tokens,
        "stream": request.stream
    }
    
    if family == "AzureOpenAI":
        if endpoint: body["endpoint"] = endpoint
        # Some azure models don't support temperature
        if deployment not in ["gpt-5", "gpt-5-mini", "gpt-5-2"]:
             body["temperature"] = request.temperature
    else:
        body["location"] = location
        body["project"] = project
        body["temperature"] = request.temperature
        
    return body

@app.get("/v1/models")
async def list_models():
    data = []
    current_time = int(time.time())
    
    # Add real models
    for name in JEDAI_MODELS.keys():
        data.append({
            "id": name,
            "object": "model",
            "created": current_time,
            "owned_by": "jedai"
        })
        
    # Add aliases
    for alias, real_name in MODEL_ALIASES.items():
        if alias not in JEDAI_MODELS: # Verify no collision
            data.append({
                "id": alias,
                "object": "model",
                "created": current_time,
                "owned_by": "jedai-alias"
            })
            
    return {"object": "list", "data": data}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    return await handle_chat_request(request)

@app.post("/v1/responses")
async def responses(request: ChatCompletionRequest):
    """Continue extension compatibility endpoint"""
    print("[INFO] Continue extension using /v1/responses endpoint")
    return await handle_chat_request(request)

async def handle_chat_request(request: ChatCompletionRequest):
    token = auth.get_token()
    url = f"{auth.connected_url}/api/copilot/v1/llm/chat/completions"
    
    jedai_body = await build_jedai_body(request)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    if request.stream:
        async def stream_generator():
            timeout = httpx.Timeout(300.0, connect=60.0)
            async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
                retry_count = 1
                while True:
                    request_headers = headers.copy()
                    
                    try:
                         async with client.stream("POST", url, json=jedai_body, headers=request_headers) as resp:
                            if resp.status_code in [401, 403] and retry_count > 0:
                                # Break context to handle retry
                                pass
                            elif resp.status_code != 200:
                                content = await resp.aread()
                                err_data = json.dumps({"error": f"Upstream error {resp.status_code}: {content.decode()}"})
                                yield f"data: {err_data}\n\n"
                                return
                            else:
                                async for chunk in resp.aiter_lines():
                                    if chunk:
                                        # JEDAI might filter keep-alives?
                                        yield chunk + "\n\n"
                                return
                    except Exception as e:
                        err_data = json.dumps({"error": f"Stream error: {str(e)}"})
                        yield f"data: {err_data}\n\n"
                        return

                    # Retry logic (outside inner async with)
                    if retry_count > 0:
                        print("Token expired (stream), refreshing...")
                        auth.clear_token()
                        auth.connect(force=True)
                        new_token = auth.get_token()
                        headers["Authorization"] = f"Bearer {new_token}"
                        retry_count -= 1
                    else:
                        return

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    else:
        # Non-streaming request
        async def do_request(retry=True):
            timeout = httpx.Timeout(300.0, connect=60.0)
            async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
                resp = await client.post(url, json=jedai_body, headers=headers)
                if resp.status_code in [401, 403] and retry:
                    return "RETRY"
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                return JSONResponse(content=resp.json())

        result = await do_request()
        if result == "RETRY":
            print("Token expired, refreshing...")
            auth.clear_token()
            auth.connect(force=True)
            token = auth.get_token()
            headers["Authorization"] = f"Bearer {token}"
            result = await do_request(retry=False)
        
        return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11434)
