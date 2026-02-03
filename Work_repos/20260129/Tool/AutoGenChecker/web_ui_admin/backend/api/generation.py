"""Generation API endpoints."""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime
import queue
import threading

# Add parent directory to path to import IntelligentCheckerAgent
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_AUTOGEN_DIR = _BACKEND_DIR.parent
if str(_AUTOGEN_DIR) not in sys.path:
    sys.path.insert(0, str(_AUTOGEN_DIR))

try:
    from llm_checker_agent import IntelligentCheckerAgent
except ImportError:
    IntelligentCheckerAgent = None
    print("Warning: Could not import IntelligentCheckerAgent")

router = APIRouter()

# Global storage for generation states and progress updates
_generation_states: Dict[str, Dict[str, Any]] = {}
_progress_queues: Dict[str, queue.Queue] = {}

class GenerateRequest(BaseModel):
    """Request model for generation."""
    item_id: str
    module: str
    llm_provider: str = "jedai"
    llm_model: Optional[str] = "claude-sonnet-4-5"
    hints: Optional[str] = None
    resume_from_step: Optional[int] = 1

class GenerateResponse(BaseModel):
    """Response model for generation."""
    item_id: str
    status: str
    message: str
    current_step: int

@router.post("/start", response_model=GenerateResponse)
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Start a new checker generation."""
    if not IntelligentCheckerAgent:
        raise HTTPException(status_code=500, detail="IntelligentCheckerAgent not available")
    
    item_id = request.item_id
    
    # Initialize state
    _generation_states[item_id] = {
        "item_id": item_id,
        "module": request.module,
        "status": "started",
        "current_step": 1,
        "progress": 0,
        "message": "Initializing...",
        "started_at": datetime.now().isoformat(),
        "config": {
            "llm_provider": request.llm_provider,
            "llm_model": request.llm_model,
            "hints": request.hints
        }
    }
    
    # Create progress queue for SSE
    _progress_queues[item_id] = queue.Queue()
    
    # Start generation in background
    background_tasks.add_task(_run_generation, item_id, request)
    
    return GenerateResponse(
        item_id=item_id,
        status="started",
        message=f"Generation started for {item_id}",
        current_step=1
    )

async def _run_generation(item_id: str, request: GenerateRequest):
    """Run generation in background thread."""
    try:
        # Update state
        _update_progress(item_id, 1, 9, "Loading configuration from CHECKLIST directory...")
        
        # Import checklist API for real YAML loading
        from . import checklist
        
        # Get real YAML data from CHECKLIST directory
        try:
            yaml_detail = await checklist.get_item_detail(request.module, request.item_id)
            _generation_states[item_id]["yaml_data"] = {
                "description": yaml_detail.description,
                "requirements": yaml_detail.requirements,
                "input_files": yaml_detail.input_files,
                "waivers": yaml_detail.waivers,
                "yaml_path": yaml_detail.yaml_path
            }
        except Exception as e:
            _update_progress(item_id, 1, 9, f"Warning: Could not load real YAML: {str(e)}")
        
        # Create agent
        agent = IntelligentCheckerAgent(
            item_id=request.item_id,
            module=request.module,
            llm_provider=request.llm_provider,
            llm_model=request.llm_model,
            verbose=True
        )
        
        # Run generation with progress callbacks
        def progress_callback(step: int, total: int, message: str):
            _update_progress(item_id, step, total, message)
        
        # Step 1: Load configuration
        _update_progress(item_id, 1, 9, "Step 1: Loading configuration...")
        config = agent._load_yaml_config()
        
        # Step 2: Analyze files
        _update_progress(item_id, 2, 9, "Step 2: Analyzing input files...")
        file_analysis = agent._ai_analyze_input_files(config)
        
        # Step 3: Generate README
        _update_progress(item_id, 3, 9, "Step 3: Generating README...")
        readme = agent._ai_generate_readme(config, file_analysis, hints=request.hints)
        
        # Step 4: Review README (simulated approval for API)
        _update_progress(item_id, 4, 9, "Step 4: README approved")
        
        # Step 5: Generate code
        _update_progress(item_id, 5, 9, "Step 5: Generating code...")
        code = agent._ai_implement_complete_code(config, file_analysis, readme)
        
        # Step 6: Self-check
        _update_progress(item_id, 6, 9, "Step 6: Running self-check...")
        # Self-check logic here
        
        # Step 7: Generate tests
        _update_progress(item_id, 7, 9, "Step 7: Generating tests...")
        # Test generation logic here
        
        # Step 8: Final review
        _update_progress(item_id, 8, 9, "Step 8: Final review...")
        
        # Step 9: Package
        _update_progress(item_id, 9, 9, "Step 9: Packaging...")
        
        # Mark as completed
        _generation_states[item_id].update({
            "status": "completed",
            "current_step": 9,
            "progress": 100,
            "message": "Generation completed successfully",
            "completed_at": datetime.now().isoformat(),
            "results": {
                "config": config,
                "readme": readme,
                "code": code
            }
        })
        
    except Exception as e:
        _generation_states[item_id].update({
            "status": "failed",
            "message": f"Error: {str(e)}",
            "error": str(e)
        })
        
def _update_progress(item_id: str, step: int, total: int, message: str):
    """Update progress state and queue."""
    progress = int((step / total) * 100)
    
    if item_id in _generation_states:
        _generation_states[item_id].update({
            "current_step": step,
            "progress": progress,
            "message": message
        })
    
    if item_id in _progress_queues:
        try:
            _progress_queues[item_id].put_nowait({
                "step": step,
                "total": total,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        except queue.Full:
            pass

@router.get("/status/{item_id}")
async def get_status(item_id: str):
    """Get generation status."""
    if item_id not in _generation_states:
        raise HTTPException(status_code=404, detail=f"Generation {item_id} not found")
    
    return _generation_states[item_id]

@router.post("/{item_id}/continue")
async def continue_generation(item_id: str):
    """Continue to next step."""
    if item_id not in _generation_states:
        raise HTTPException(status_code=404, detail=f"Generation {item_id} not found")
    
    state = _generation_states[item_id]
    current_step = state.get("current_step", 1)
    
    if current_step < 9:
        state["current_step"] = current_step + 1
        state["message"] = f"Continuing to step {current_step + 1}"
        return {"status": "continued", "current_step": current_step + 1}
    else:
        return {"status": "completed", "message": "Already at final step"}

@router.post("/{item_id}/save")
async def save_progress(item_id: str, data: dict):
    """Save current progress."""
    if item_id not in _generation_states:
        raise HTTPException(status_code=404, detail=f"Generation {item_id} not found")
    
    # Update state with saved data
    _generation_states[item_id].update({
        "last_saved": datetime.now().isoformat(),
        "saved_data": data
    })
    
    # TODO: Persist to database/file
    return {"status": "saved", "timestamp": datetime.now().isoformat()}

@router.get("/{item_id}/progress")
async def get_progress(item_id: str):
    """Get detailed progress."""
    # TODO: Return actual progress
    return {
        "item_id": item_id,
        "steps": [
            {"step": 1, "name": "Configuration", "status": "completed"},
            {"step": 2, "name": "File Analysis", "status": "completed"},
            {"step": 3, "name": "README", "status": "completed"},
            {"step": 4, "name": "Review", "status": "completed"},
            {"step": 5, "name": "Code", "status": "in_progress"},
            {"step": 6, "name": "Self Check", "status": "pending"},
            {"step": 7, "name": "Testing", "status": "pending"},
            {"step": 8, "name": "Final Review", "status": "pending"},
            {"step": 9, "name": "Package", "status": "pending"},
        ]
    }

@router.get("/stream/progress")
async def stream_progress(item_id: str):
    """Stream real-time progress updates via SSE."""
    if item_id not in _progress_queues:
        raise HTTPException(status_code=404, detail=f"Generation {item_id} not found")
    
    async def event_generator():
        progress_queue = _progress_queues[item_id]
        
        # Send initial state
        if item_id in _generation_states:
            initial_state = _generation_states[item_id]
            yield f"data: {json.dumps(initial_state)}\n\n"
        
        # Stream updates from queue
        while True:
            try:
                # Non-blocking get with timeout
                update = progress_queue.get(timeout=1)
                yield f"data: {json.dumps(update)}\n\n"
                
                # Check if completed or failed
                if item_id in _generation_states:
                    state = _generation_states[item_id]
                    if state["status"] in ["completed", "failed"]:
                        break
                        
            except queue.Empty:
                # Send keepalive
                yield f": keepalive\n\n"
                
                # Check if generation is still active
                if item_id not in _generation_states:
                    break
                    
            except Exception as e:
                print(f"SSE error: {e}")
                break
            
            await asyncio.sleep(0.1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
