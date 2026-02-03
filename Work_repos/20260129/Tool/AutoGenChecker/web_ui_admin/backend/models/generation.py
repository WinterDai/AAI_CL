"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StepStatus(str, Enum):
    """Step status enum."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerationStatus(str, Enum):
    """Generation status enum."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowStep(BaseModel):
    """Workflow step model."""
    step: int
    name: str
    status: StepStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    error: Optional[str] = None

class FileAnalysis(BaseModel):
    """File analysis result model."""
    filename: str
    file_type: str
    lines: int
    size: int
    patterns: List[str] = []
    sample_data: str = ""
    status: str = "passed"

class TestResult(BaseModel):
    """Test result model."""
    test_type: int
    description: str
    status: str  # "PASSED", "FAILED", "ERROR", "PENDING"
    time: Optional[float] = None
    log: Optional[str] = None
    error: Optional[str] = None

class GenerationState(BaseModel):
    """Complete generation state."""
    item_id: str
    module: str
    status: GenerationStatus
    current_step: int
    progress: int  # 0-100
    steps: List[WorkflowStep] = []
    config: Dict[str, Any] = {}
    file_analysis: List[FileAnalysis] = []
    generated_readme: Optional[str] = None
    generated_code: Optional[str] = None
    generated_yaml: Optional[str] = None
    test_results: List[TestResult] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
