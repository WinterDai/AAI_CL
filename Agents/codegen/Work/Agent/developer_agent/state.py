"""
Developer Agent - State Definitions
Based on Agent_Development_Spec.md v1.1

Defines the AgentState TypedDict and related configuration classes.
"""
from typing import TypedDict, List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import yaml
import os


class AgentState(TypedDict):
    """
    LangGraph State Definition for Developer Agent
    
    This state is passed between all nodes in the graph and persisted to cache.
    """
    # === Input Context ===
    item_spec_path: str                    # ItemSpec file path (e.g., "IMP-10-0-0-00_ItemSpec.md")
    item_spec_content: str                 # ItemSpec raw content (dynamically loaded)
    parsed_spec: Dict[str, Any]            # Parsed ItemSpec structure
    
    # === Tool Retrieval Results ===
    discovered_log_files: List[str]        # Log file paths discovered via tools
    log_snippets: Dict[str, Any]           # {file_path: snippet_content} real log snippets
    
    # === Agent A Output ===
    atom_a_code: str                       # extract_context function code
    atom_a_reasoning: str                  # Agent A reasoning process (for debugging)
    
    # === Agent B Output ===
    atom_b_code: str                       # validate_logic function code
    atom_c_code: str                       # check_existence function code
    yaml_config: str                       # Generated YAML configuration
    atom_b_reasoning: str                  # Agent B reasoning process
    
    # === Validation Results ===
    validation_errors: List[str]           # Error list returned by Validator
    gate_results: Dict[str, bool]          # {"gate1": True, "gate2": False, ...}
    error_source: str                      # "atom_a" | "atom_b" | "atom_c" | "yaml" | "unknown"
    
    # === Control Flow ===
    current_stage: str                     # "init" | "discover" | "agent_a" | "agent_b" | "validate" | "reflect_a" | "reflect_b" | "done" | "human_required"
    iteration_count: int                   # Current retry count (Max: 3)
    checkpoint_id: str                     # Cache checkpoint ID (for recovery)
    
    # === Metadata ===
    created_at: str                        # ISO timestamp
    updated_at: str                        # ISO timestamp
    error_history: List[Dict[str, Any]]    # Historical error records (for Reflect)
    
    # === Multi-turn Context Maintenance ===
    conversation_summary: str              # Accumulated context summary (avoid forgetting)
    generated_code_signatures: Dict[str, str]  # {function_name: signature} cache
    key_decisions: List[Dict[str, str]]    # [{"round": "1", "decision": "...", "reason": "..."}]
    iteration_context: Dict[str, Any]      # Context passed between iterations


@dataclass
class LLMConfig:
    """LLM Configuration"""
    provider: str
    model: str
    temperature: float
    max_tokens: int


@dataclass
class AgentConfig:
    """
    Agent Runtime Configuration
    Loaded from agent_config.yaml
    """
    search_root: str
    item_specs_dir: str
    cache_dir: str
    output_dir: str
    agent_a_llm: LLMConfig
    agent_b_llm: LLMConfig
    reflect_llm: LLMConfig
    max_iterations: int
    cache_retention_policy: str
    max_checkpoints_per_hour: int
    log_level: str
    log_file: str
    log_llm_calls: bool
    
    @classmethod
    def load(cls, config_path: str = None) -> "AgentConfig":
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            # Default: look for config in same directory as this module
            module_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(module_dir, "config", "agent_config.yaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        
        return cls(
            search_root=cfg['paths']['search_root'],
            item_specs_dir=cfg['paths']['item_specs_dir'],
            cache_dir=cfg['paths']['cache_dir'],
            output_dir=cfg['paths']['output_dir'],
            agent_a_llm=LLMConfig(**cfg['llm']['agent_a']),
            agent_b_llm=LLMConfig(**cfg['llm']['agent_b']),
            reflect_llm=LLMConfig(**cfg['llm']['reflect']),
            max_iterations=cfg['execution']['max_iterations'],
            cache_retention_policy=cfg['cache']['retention_policy'],
            max_checkpoints_per_hour=cfg['cache']['max_checkpoints_per_hour'],
            log_level=cfg['logging']['level'],
            log_file=cfg['logging']['log_file'],
            log_llm_calls=cfg['logging']['log_llm_calls']
        )


def create_initial_state(item_spec_path: str, search_root: str = None) -> AgentState:
    """
    Create a fresh AgentState for a new run
    
    Args:
        item_spec_path: Path to the ItemSpec file
        search_root: Override for search_root (optional)
    """
    now = datetime.now().isoformat()
    
    return AgentState(
        # Input Context
        item_spec_path=item_spec_path,
        item_spec_content="",
        parsed_spec={},
        
        # Tool Retrieval Results
        discovered_log_files=[],
        log_snippets={},
        
        # Agent A Output
        atom_a_code="",
        atom_a_reasoning="",
        
        # Agent B Output
        atom_b_code="",
        atom_c_code="",
        yaml_config="",
        atom_b_reasoning="",
        
        # Validation Results
        validation_errors=[],
        gate_results={},
        error_source="",
        
        # Control Flow
        current_stage="init",
        iteration_count=0,
        checkpoint_id="",
        
        # Metadata
        created_at=now,
        updated_at=now,
        error_history=[],
        
        # Multi-turn Context Maintenance
        conversation_summary="",
        generated_code_signatures={},
        key_decisions=[],
        iteration_context={}
    )


def generate_item_id(item_spec_path: str) -> str:
    """
    Generate a unique item_id from ItemSpec path
    
    Args:
        item_spec_path: Path to ItemSpec file
        
    Returns:
        Sanitized item_id string (e.g., "IMP-10-0-0-00")
        
    Examples:
        "items/IMP-10-0-0-00.yaml" -> "IMP-10-0-0-00"
        "path/to/ABC-1-2-3-04_ItemSpec.md" -> "ABC-1-2-3-04"
        "IMP-10-0-0-00.yml" -> "IMP-10-0-0-00"
    """
    base_name = os.path.basename(item_spec_path)
    # Remove various extensions
    result = base_name
    for ext in ["_ItemSpec.md", ".md", ".yaml", ".yml"]:
        result = result.replace(ext, "")
    # Sanitize path separators
    result = result.replace("/", "_").replace("\\", "_")
    return result
