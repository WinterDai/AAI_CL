"""FastAPI backend for AutoGenChecker Web UI."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pathlib import Path
import sys

# Add AutoGenChecker root to path for imports (utils, workflow, etc.)
# Path: app.py -> backend/ -> web_ui/ -> AutoGenChecker/
_backend_dir = Path(__file__).parent
_autogen_root = _backend_dir.parent.parent  # AutoGenChecker root
if str(_autogen_root) not in sys.path:
    sys.path.insert(0, str(_autogen_root))
    print(f"[app.py] Added to sys.path: {_autogen_root}")

# Debug: Print current sys.path
print(f"[app.py] sys.path[0]: {sys.path[0]}")
print(f"[app.py] Loading routers...")

from api import generation, history, templates, settings, dashboard
from api.workflow_integration import router as workflow_router

# Import step routers with error handling
try:
    from api.steps import (
        step1_router, step2_router, step3_router, 
        step4_router, step5_router, step6_router,
        step7_router, step8_router, step9_router
    )
    print(f"[app.py] ✓ All step routers loaded successfully")
    print(f"[app.py]   step9_router routes: {[r.path for r in step9_router.routes]}")
except Exception as e:
    print(f"[app.py] ✗ Failed to load step routers: {e}")
    import traceback
    traceback.print_exc()
    raise

app = FastAPI(
    title="AutoGenChecker API",
    description="Backend API for AutoGenChecker Web UI",
    version="1.0.0"
)

# Add custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[VALIDATION ERROR] Path: {request.url.path}")
    print(f"[VALIDATION ERROR] Method: {request.method}")
    print(f"[VALIDATION ERROR] Errors: {exc.errors()}")
    try:
        body = await request.body()
        print(f"[VALIDATION ERROR] Body: {body.decode()[:500]}")
    except:
        pass
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Alternative localhost
        "*"  # Allow all origins in development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API routers
app.include_router(generation.router, prefix="/api/generation", tags=["generation"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(dashboard.router, tags=["dashboard"])

# Step-by-step routers (aligned with CLI workflow)
app.include_router(step1_router, prefix="/api/step1", tags=["step1-config"])
app.include_router(step2_router, prefix="/api/step2", tags=["step2-file-analysis"])
app.include_router(step3_router, prefix="/api/step3", tags=["step3-readme"])
app.include_router(step4_router, prefix="/api/step4", tags=["step4-review"])
app.include_router(step5_router, prefix="/api/step5", tags=["step5-code"])
app.include_router(step6_router, prefix="/api/step6", tags=["step6-selfcheck"])
app.include_router(step7_router, prefix="/api/step7", tags=["step7-testing"])
app.include_router(step8_router, prefix="/api/step8", tags=["step8-final-review"])
app.include_router(step9_router, prefix="/api/step9", tags=["step9-package"])

# Workflow integration router (Dispatch/Development/Collection)
app.include_router(workflow_router, prefix="/api/workflow", tags=["workflow"])

# Backward compatibility: Keep old /api/checklist endpoints as aliases
# Redirect to new step endpoints
app.include_router(step1_router, prefix="/api/checklist", tags=["checklist-compat"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AutoGenChecker API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
