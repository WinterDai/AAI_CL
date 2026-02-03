"""Data models for workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class WorkflowConfig:
    """Configuration for the checker generation workflow."""
    
    item_id: str
    module: str
    item_desc: Optional[str] = None
    input_files: list[str] = field(default_factory=list)
    
    # LLM settings
    use_llm: bool = True
    llm_provider: str = "openai"
    llm_model: Optional[str] = None
    temperature: float = 0.3
    
    # Workflow control
    interactive: bool = False
    force_file_analysis: bool = True  # Step 2.5 is mandatory
    skip_readme: bool = False
    skip_test_setup: bool = False
    
    # Output paths
    output_dir: Optional[Path] = None


@dataclass
class CheckerArtifacts:
    """Output artifacts from the checker generation workflow."""
    
    config: dict[str, Any]
    readme: Optional[str] = None
    code: Optional[str] = None
    test_artifacts: Optional[dict[str, Any]] = None
    file_analysis: list[dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    workflow_steps_completed: list[str] = field(default_factory=list)
    time_taken_seconds: float = 0.0
    manual_refinement_needed: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'config': self.config,
            'readme': self.readme,
            'code': self.code,
            'test_artifacts': self.test_artifacts,
            'file_analysis': self.file_analysis,
            'workflow_steps_completed': self.workflow_steps_completed,
            'time_taken_seconds': self.time_taken_seconds,
            'manual_refinement_needed': self.manual_refinement_needed,
        }
