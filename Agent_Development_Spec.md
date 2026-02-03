# Agent Development Specification v1.0

**Goal**: Build a universal Developer Agent that can automatically generate Atom code compliant with Architecture 10.2 based on **any ItemSpec**.

**Core Principles**:
1. **Zero Hardcoding**: Agent must not contain any item-specific hardcoded content
2. **Cache-First**: All intermediate states must be persisted, supporting checkpoint recovery
3. **Tool-Driven**: Agent dynamically retrieves real log samples through **active tool calls**, tool calls are constrained by framework
4. **Human-in-the-Loop**: Must request human intervention when failure limit is exceeded
5. **ItemSpec as Guidance**: ItemSpec is reference only, Agent must make autonomous decisions based on actual observed data

---

## 1. System Architecture

### 1.1 Overall Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agent Orchestrator                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ ItemSpec │───▶│  Agent A │───▶│  Agent B │───▶│ Validator│             │
│   │  Loader  │    │ (Parser) │    │ (Logic)  │    │  (Gate)  │             │
│   └──────────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│         │              │               │               │                    │
│         ▼              ▼               ▼               ▼                    │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                      State Cache Layer                           │      │
│   │  (checkpoint_id, stage, inputs, outputs, errors, timestamp)      │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 LangGraph State Definition

```python
# === Complete Import Statements ===
from typing import TypedDict, List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import os
import re
import json
import yaml
import ast
import glob
import shutil
import gzip

from langgraph.graph import StateGraph, END

# Prompt Template Constants (defined in Section 4)
AGENT_A_PROMPT_TEMPLATE: str
AGENT_B_PROMPT_TEMPLATE: str
REFLECT_PROMPT_TEMPLATE: str


class AgentState(TypedDict):
    # === Input Context ===
    item_spec_path: str                    # ItemSpec file path (e.g., "IMP-10-0-0-00_ItemSpec.md")
    item_spec_content: str                 # ItemSpec raw content (dynamically loaded)
    
    # === Tool Retrieval Results ===
    discovered_log_files: List[str]        # Log file paths discovered via tools
    log_snippets: Dict[str, str]           # {file_path: snippet_content} real log snippets
    
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
    error_source: str                      # "atom_a" | "atom_b" | "atom_c" | "yaml" | "unknown" (for smart repair)
    
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
```

### 1.3 Graph Node Definition

```
                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Load Spec   │  <- Load ItemSpec, parse and separate Sections
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Preprocess │  <- Framework auto: resolve path vars ${VAR}, init tools
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Agent A   │  <- Input: Section 1 + 4.1 + Tools
                    │   (Draft)   │     LLM actively calls tools to read logs, generate extract_context
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Agent B   │  <- Input: Section 2 + 3 + 4.2 + Agent A Code + YAML Template
                    │   (Draft)   │     Generate validate_logic + check_existence + YAML config
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Validator  │  ← AST Check + Runtime Sandbox + Consistency Check
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │   PASS   │     │   FAIL   │     │   FAIL   │
   │  (Done)  │     │ (iter<3) │     │ (iter≥3) │
   └──────────┘     └─────┬────┘     └────┬─────┘
                         │                 │
         ┌───────────────┴─────────────┐ │
         │ determine_error_source()  │ │
         └─────────────┬─────────────┘ │
                       │               │
         ┌─────────────┴───────────┐ │
         │                         │ │
         ▼                         ▼ ▼
   ┌───────────┐           ┌───────────┐ ┌───────────┐
   │ Reflect_A │           │ Reflect_B │ │  Human   │
   │ (Atom A)  │           │(B/C/YAML)│ │ Required │
   └─────┬─────┘           └─────┬─────┘ └───────────┘
         │                         │
         ▼                         ▼
   ┌───────────┐           ┌───────────┐
   │  Agent A  │           │  Agent B  │
   │(Rerun All)│           │(Reuse A)  │
   └───────────┘           └───────────┘
```

---

## 1.4 Configuration File Structure

Agent obtains environment parameters through configuration files at runtime, avoiding hardcoding.

**Configuration File Path**: `./config/agent_config.yaml`

```yaml
# agent_config.yaml - Agent Runtime Configuration

# === Path Configuration ===
paths:
  search_root: "/project/design"              # Log file search root directory
  item_specs_dir: "./item_specs"              # ItemSpec files directory
  cache_dir: "./cache"                        # Cache storage directory
  output_dir: "./output"                      # Generated code output directory

# === LLM Model Configuration ===
llm:
  # Agent A (Parsing Expert) Model Configuration
  agent_a:
    provider: "openai"                        # openai | anthropic | azure
    model: "gpt-4-turbo"                      # Model name
    temperature: 0.2                          # Low temperature ensures code stability
    max_tokens: 4096
  
  # Agent B (Logic Expert) Model Configuration
  agent_b:
    provider: "openai"
    model: "gpt-4-turbo"
    temperature: 0.1                          # Lower temperature, logic code needs determinism
    max_tokens: 4096
  
  # Reflect Node Model Configuration (can use faster model)
  reflect:
    provider: "openai"
    model: "gpt-4-turbo"                      # Or "gpt-3.5-turbo" for faster iteration
    temperature: 0.1
    max_tokens: 2048

# === Cache Configuration ===
cache:
  retention_policy: "hourly"                  # Save checkpoints hourly
  max_checkpoints_per_hour: 10                # Max checkpoints to keep per hour
  cleanup_on_success: false                   # Whether to clean up historical checkpoints on success
  
# === Execution Control ===
execution:
  max_iterations: 3                           # Max retry count
  timeout_per_stage: 300                      # Timeout per stage (seconds)
  enable_streaming: true                      # Whether to enable streaming output

# === Logging Configuration ===
logging:
  level: "INFO"                               # DEBUG | INFO | WARNING | ERROR
  log_file: "./logs/agent.log"
  log_llm_calls: true                         # Whether to log LLM call details

# === Tool Call Constraints ===
tool_constraints:
  max_read_lines_per_call: 200                # Max lines per single read
  max_total_read_bytes: 102400                # Total read bytes per session (100KB)
  require_discovery_before_read: true         # Must discover before read
  header_lines_default: 100                   # Default header lines to read
```

---

### 1.5 Agent Input Scope Definition (CRITICAL)

**Information Isolation Principle**: Each Agent should only see ItemSpec Sections relevant to its responsibilities, avoiding information interference.

| Agent | Visible ItemSpec Sections | Forbidden | Additional Input |
|-------|----------------------|---------|----------|
| **Agent A** | Section 1 (Parsing Logic) + Section 4.1 (Data Source & Extraction) | Section 2, 3, 4.2, 4.3 | Tools (constrained), framework-preprocessed paths |
| **Agent B** | Section 2 (Check Logic) + Section 3 (Waiver Logic) + Section 4.2 (Special Scenarios) | Section 1, 4.1, 4.3 | Agent A code, YAML empty template |

**About Runtime Configuration Values**:
- Agent **can know** that fields like `requirements`, `waivers`, `pattern_items` **exist**
- Agent **is forbidden from seeing** the **actual runtime values** of these fields (e.g., `requirements.value = 2`)
- YAML template should show **structure**, values replaced with placeholder `<TO_BE_INFERRED>`

**Agent A Autonomy**:
- ItemSpec Section 1 + 4.1 is **reference guidance only**
- Agent A must make autonomous decisions based on **actually observed log content**
- If Agent A discovers references to other files in logs (e.g., SPEF path in STA log), Agent A **may actively call tools** to read those files

**Configuration Loader**:

```python
import yaml
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int

@dataclass
class AgentConfig:
    search_root: str
    item_specs_dir: str
    cache_dir: str
    output_dir: str
    agent_a_llm: LLMConfig
    agent_b_llm: LLMConfig
    reflect_llm: LLMConfig
    max_iterations: int
    cache_retention_policy: str
    
    @classmethod
    def load(cls, config_path: str = "./config/agent_config.yaml") -> "AgentConfig":
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
            cache_retention_policy=cfg['cache']['retention_policy']
        )


def get_llm_client(config: LLMConfig):
    """
    Create LLM client and call parameters based on configuration.
    Supports: OpenAI, Anthropic, Azure
    
    Returns:
        tuple: (client, call_params) client instance and call parameters
    """
    call_params = {
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens
    }
    
    if config.provider == "openai":
        from openai import OpenAI
        return OpenAI(), call_params
    elif config.provider == "anthropic":
        from anthropic import Anthropic
        return Anthropic()
    elif config.provider == "azure":
        from openai import AzureOpenAI
        return AzureOpenAI()
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")
```

---

## 2. Cache Mechanism Design

### 2.1 Cache Storage Structure

**Directory structure organized by hour** (for easy cleanup and rollback):

```
cache/
├── {item_id}/
│   ├── checkpoint_latest.json           # Latest checkpoint (for quick recovery)
│   ├── hourly/
│   │   ├── 2026012814/                   # Grouped by hour (YYYYMMDDHH)
│   │   │   ├── checkpoint_143025.json    # Timestamp checkpoint (HHMMSS)
│   │   │   ├── checkpoint_144512.json
│   │   │   └── ...
│   │   ├── 2026012815/
│   │   │   └── ...
│   │   └── ...
│   ├── stage_outputs/
│   │   ├── load_spec.json                # ItemSpec parse result
│   │   ├── discover_logs.json            # Discovered log files and snippets
│   │   ├── agent_a_output.json           # Agent A output (code + reasoning)
│   │   ├── agent_b_output.json           # Agent B output (code + yaml + reasoning)
│   │   └── validation_result.json        # Validation result
│   └── error_logs/
│       └── iteration_{n}.json            # Error details for iteration n
```

### 2.2 Cache Operation Interface

```python
from abc import ABC, abstractmethod
from typing import Optional
import json
import os
from datetime import datetime, timedelta

class StateCache(ABC):
    """State cache abstract interface"""
    
    @abstractmethod
    def save_checkpoint(self, item_id: str, state: AgentState) -> str:
        """Save checkpoint, return checkpoint_id"""
        pass
    
    @abstractmethod
    def load_checkpoint(self, item_id: str, checkpoint_id: Optional[str] = None) -> Optional[AgentState]:
        """Load checkpoint, defaults to latest"""
        pass
    
    @abstractmethod
    def save_stage_output(self, item_id: str, stage: str, output: dict) -> None:
        """Save single stage output"""
        pass
    
    @abstractmethod
    def load_stage_output(self, item_id: str, stage: str) -> Optional[dict]:
        """Load single stage output"""
        pass


class FileSystemCache(StateCache):
    """File system based cache implementation (hourly save)"""
    
    def __init__(self, cache_dir: str = "./cache", max_checkpoints_per_hour: int = 10):
        self.cache_dir = cache_dir
        self.max_checkpoints_per_hour = max_checkpoints_per_hour
    
    def save_checkpoint(self, item_id: str, state: AgentState) -> str:
        now = datetime.now()
        hour_folder = now.strftime("%Y%m%d%H")  # e.g., "2026012814"
        checkpoint_id = now.strftime("%H%M%S")   # e.g., "143025"
        
        item_dir = os.path.join(self.cache_dir, item_id)
        hourly_dir = os.path.join(item_dir, "hourly", hour_folder)
        os.makedirs(hourly_dir, exist_ok=True)
        
        # Save to hourly grouped directory
        checkpoint_path = os.path.join(hourly_dir, f"checkpoint_{checkpoint_id}.json")
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(dict(state), f, indent=2, ensure_ascii=False)
        
        # Update latest checkpoint
        latest_path = os.path.join(item_dir, "checkpoint_latest.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(dict(state), f, indent=2, ensure_ascii=False)
        
        # Clean up excess checkpoints in current hour
        self._cleanup_hourly_checkpoints(hourly_dir)
        
        return f"{hour_folder}_{checkpoint_id}"
    
    def _cleanup_hourly_checkpoints(self, hourly_dir: str) -> None:
        """Keep only N most recent checkpoints per hour"""
        checkpoints = sorted([
            f for f in os.listdir(hourly_dir) 
            if f.startswith("checkpoint_") and f.endswith(".json")
        ])
        
        if len(checkpoints) > self.max_checkpoints_per_hour:
            for old_checkpoint in checkpoints[:-self.max_checkpoints_per_hour]:
                os.remove(os.path.join(hourly_dir, old_checkpoint))
                print(f"[Cache] Cleaned up old checkpoint: {old_checkpoint}")
    
    def cleanup_old_hours(self, item_id: str, keep_hours: int = 24) -> None:
        """
        Clean up historical checkpoint directories older than specified hours.
        
        Args:
            item_id: Item identifier
            keep_hours: How many hours of data to keep
        """
        hourly_base = os.path.join(self.cache_dir, item_id, "hourly")
        if not os.path.exists(hourly_base):
            return
        
        cutoff = datetime.now() - timedelta(hours=keep_hours)
        cutoff_folder = cutoff.strftime("%Y%m%d%H")
        
        for folder in os.listdir(hourly_base):
            if folder < cutoff_folder:
                folder_path = os.path.join(hourly_base, folder)
                import shutil
                shutil.rmtree(folder_path)
                print(f"[Cache] Removed old hourly folder: {folder}")
    
    def load_checkpoint(self, item_id: str, checkpoint_id: Optional[str] = None) -> Optional[AgentState]:
        """
        Load checkpoint.
        
        Args:
            item_id: Item identifier
            checkpoint_id: Checkpoint ID, format "{hour_folder}_{time}" (e.g., "2026012814_143025")
                          If None, loads latest checkpoint
        """
        item_dir = os.path.join(self.cache_dir, item_id)
        
        if checkpoint_id:
            # Parse checkpoint_id format: {hour_folder}_{time}
            if "_" in checkpoint_id:
                parts = checkpoint_id.split("_")
                if len(parts) >= 2:
                    hour_folder = parts[0]  # e.g., "2026012814"
                    time_part = parts[1]     # e.g., "143025"
                    path = os.path.join(item_dir, "hourly", hour_folder, f"checkpoint_{time_part}.json")
                else:
                    path = os.path.join(item_dir, f"checkpoint_{checkpoint_id}.json")
            else:
                path = os.path.join(item_dir, f"checkpoint_{checkpoint_id}.json")
        else:
            path = os.path.join(item_dir, "checkpoint_latest.json")
        
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_stage_output(self, item_id: str, stage: str, output: dict) -> None:
        stage_dir = os.path.join(self.cache_dir, item_id, "stage_outputs")
        os.makedirs(stage_dir, exist_ok=True)
        
        path = os.path.join(stage_dir, f"{stage}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def load_stage_output(self, item_id: str, stage: str) -> Optional[dict]:
        path = os.path.join(self.cache_dir, item_id, "stage_outputs", f"{stage}.json")
        
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
```

### 2.3 Checkpoint Recovery Logic

```python
def resume_from_checkpoint(item_id: str, cache: StateCache) -> AgentState:
    """
    Checkpoint recovery logic:
    1. Load latest checkpoint
    2. Determine which node to continue from based on current_stage
    3. Skip completed stages, directly use cached stage_output
    """
    state = cache.load_checkpoint(item_id)
    
    if state is None:
        # No cache, start from beginning
        return create_initial_state(item_id)
    
    stage = state['current_stage']
    
    if stage == "done":
        print(f"[INFO] Item {item_id} already completed, no recovery needed")
        return state
    
    if stage == "human_required":
        print(f"[WARN] Item {item_id} requires human intervention, cannot auto-recover")
        return state
    
    print(f"[INFO] Resuming execution from stage '{stage}'")
    return state
```

---

## 3. Tool Set Definition

### 3.0 Tool Call Constraint Mechanism (CRITICAL)

**Design Principle**: LLM actively calls tools, but framework imposes constraints to prevent resource abuse.

#### 3.0.1 Layered Reading Strategy

| Layer | Tool | Constraint | Purpose |
|-----|------|-----|------|
| **Layer 0** | `resolve_paths()` | **Framework auto-call, invisible to LLM** | Resolve `${VAR}` to absolute paths |
| **Layer 1** | `list_available_files()` | Returns only paths+sizes, no content | Let LLM know what files are available |
| **Layer 2** | `read_file_header(file, max_lines=100)` | Enforced max line limit | Read version info, file structure |
| **Layer 3** | `search_in_file(file, keywords, context=10)` | Max 3 matches per keyword | Smart summary, avoid full file read |
| **Layer 4** | `read_file_range(file, start, end)` | Max 200 lines per call | On-demand precise reading |

#### 3.0.2 Quota Limits

```python
TOOL_CONSTRAINTS = {
    "max_read_lines_per_call": 200,      # Max lines per single read
    "max_total_read_bytes": 100 * 1024,  # Total read bytes per session (100KB)
    "max_files_per_discovery": 20,       # Max files per single discovery
    "max_search_matches_per_keyword": 3, # Max matches returned per keyword
    "require_discovery_before_read": True # Must discover before read
}
```

#### 3.0.3 Path Variable Preprocessing (Framework Layer)

```python
def resolve_path_variables(path: str, env_vars: Dict[str, str]) -> str:
    """
    Framework layer auto-resolves path variables, LLM only sees resolved absolute paths.
    
    Supported variables:
        ${CHECKLIST_ROOT} -> Checklist root directory
        ${DESIGN_ROOT} -> Design files root directory
        ${LOG_ROOT} -> Logs root directory
    
    This function is auto-called by framework before Tools are exposed to LLM.
    """
    import re
    result = path
    for var_name, var_value in env_vars.items():
        result = result.replace(f"${{{var_name}}}", var_value)
    return os.path.normpath(result)
```

#### 3.0.4 Tool Call Order Constraints

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Tool Calling Flow                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. list_available_files()  <- Must call first, get file list│
│            │                                                 │
│            ▼                                                 │
│  2. read_file_header()      <- Read file header, determine type│
│            │                                                 │
│            ▼                                                 │
│  3. search_in_file()        <- Search keywords, get summary   │
│            │                                                 │
│            ▼                                                 │
│  4. read_file_range()       <- On-demand read specific range  │
│                                                              │
│  FORBIDDEN: Skip step 1 and read file directly               │
│  FORBIDDEN: Read entire file at once                         │
│  FORBIDDEN: Exceed quota limits                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.1 File Listing Tool

```python
from typing import List, Dict
import os
import glob

@tool
def list_available_files(
    search_root: str,
    patterns: List[str],
    max_files: int = 20
) -> Dict[str, List[Dict]]:
    """
    List available files (without reading content), return file metadata.
    
    This is the tool LLM must call first, to know what files are available.
    
    Args:
        search_root: Search root directory (path variables resolved by framework)
        patterns: File pattern list (e.g., ["*.log", "*.spef"])
        max_files: Max files to return per pattern
    
    Returns:
        {
            "files": [
                {"path": "/abs/path/to/file.log", "size": 1024, "type": "log"},
                ...
            ],
            "total_found": 42,
            "truncated": True
        }
    """
    results = []
    for pattern in patterns:
        matches = glob.glob(os.path.join(search_root, "**", pattern), recursive=True)
        for match in matches[:max_files]:
            results.append({
                "path": match,
                "size": os.path.getsize(match),
                "type": infer_file_type(match)
            })
    
    return {
        "files": results[:max_files * len(patterns)],
        "total_found": len(results),
        "truncated": len(results) > max_files * len(patterns)
    }


def infer_file_type(path: str) -> str:
    """Infer file type based on extension"""
    ext = os.path.splitext(path)[1].lower()
    type_map = {
        '.log': 'log', '.rpt': 'report', '.v': 'netlist', '.vg': 'netlist',
        '.spef': 'spef', '.gz': 'compressed', '.yaml': 'config', '.yml': 'config'
    }
    return type_map.get(ext, 'unknown')
```

### 3.2 File Header Tool

```python
@tool
def read_file_header(
    file_path: str,
    max_lines: int = 100
) -> Dict[str, Any]:
    """
    Read file header (limited lines), for version info extraction.
    
    Args:
        file_path: File absolute path
        max_lines: Max lines to read (enforced upper limit 200)
    
    Returns:
        {
            "file_path": "/path/to/file",
            "content": "First N lines content",
            "lines_read": 100,
            "file_size": 1024,
            "encoding": "utf-8"
        }
    """
    import gzip
    
    # Enforce upper limit
    max_lines = min(max_lines, 200)
    
    if file_path.endswith('.gz'):
        with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            lines = [f.readline() for _ in range(max_lines)]
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [f.readline() for _ in range(max_lines)]
    
    content = ''.join(lines)
    
    return {
        "file_path": file_path,
        "content": content,
        "lines_read": len(lines),
        "file_size": os.path.getsize(file_path),
        "encoding": "utf-8"
    }
```

### 3.3 Keyword Search Tool (Smart Search)

```python
@tool
def search_in_file(
    file_path: str,
    keywords: List[str],
    context_lines: int = 10,
    max_matches_per_keyword: int = 3
) -> Dict[str, Any]:
    """
    Search keywords in file, return matching lines with context (smart summary).
    
    This tool avoids reading entire file, returns only keyword-related snippets.
    
    Args:
        file_path: File absolute path
        keywords: Search keyword list
        context_lines: Context lines around each match
        max_matches_per_keyword: Max matches per keyword
    
    Returns:
        {
            "file_path": "/path/to/file",
            "matches": [
                {
                    "keyword": "Reading netlist",
                    "line_number": 42,
                    "content": "... context content ..."
                },
                ...
            ],
            "total_matches": 5
        }
    """
    import gzip
    
    if file_path.endswith('.gz'):
        with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    
    matches = []
    for keyword in keywords:
        keyword_matches = 0
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower() and keyword_matches < max_matches_per_keyword:
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet = ''.join(lines[start:end])
                
                matches.append({
                    "keyword": keyword,
                    "line_number": i + 1,
                    "content": snippet[:2000]  # Truncate long content
                })
                keyword_matches += 1
    
    return {
        "file_path": file_path,
        "matches": matches,
        "total_matches": len(matches)
    }
```

### 3.4 Range Read Tool

```python
@tool
def read_file_range(
    file_path: str,
    start_line: int,
    end_line: int
) -> Dict[str, Any]:
    """
    Read specific line range from file (constrained).
    
    Used when LLM needs more context after searching.
    
    Args:
        file_path: File absolute path
        start_line: Start line number (1-based)
        end_line: End line number (1-based, inclusive)
    
    Constraints:
        - Max 200 lines per read
        - Exceeding limit will be truncated
    
    Returns:
        {
            "file_path": "/path/to/file",
            "content": "Read content",
            "start_line": 100,
            "end_line": 200,
            "truncated": False
        }
    """
    import gzip
    
    # Enforce upper limit
    max_lines = 200
    if end_line - start_line + 1 > max_lines:
        end_line = start_line + max_lines - 1
        truncated = True
    else:
        truncated = False
    
    if file_path.endswith('.gz'):
        with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    
    # Convert to 0-based index
    selected = lines[start_line - 1:end_line]
    content = ''.join(selected)
    
    return {
        "file_path": file_path,
        "content": content,
        "start_line": start_line,
        "end_line": min(end_line, len(lines)),
        "truncated": truncated
    }
```

### 3.5 ItemSpec Section Extraction Tool (Framework Internal Use)

```python
def extract_itemspec_sections(spec_content: str) -> Dict[str, str]:
    """
    Extract each Section content from ItemSpec (framework internal use).
    
    Used to implement information isolation: Agent A can only see Section 1 + 4.1.
    
    Returns:
        {
            "section_1": "Parsing Logic content...",
            "section_2": "Check Logic content...",
            "section_3": "Waiver Logic content...",
            "section_4_1": "Data Source & Extraction content...",
            "section_4_2": "Special Scenario content...",
            "section_4_3": "Test Data Generation content..."
        }
    """
    import re
    
    sections = {}
    
    # Extract Section 1
    match = re.search(r'## 1\. Parsing Logic(.*?)(?=## 2\.)', spec_content, re.DOTALL)
    sections["section_1"] = match.group(1).strip() if match else ""
    
    # Extract Section 2
    match = re.search(r'## 2\. Check Logic(.*?)(?=## 3\.)', spec_content, re.DOTALL)
    sections["section_2"] = match.group(1).strip() if match else ""
    
    # Extract Section 3
    match = re.search(r'## 3\. Waiver Logic(.*?)(?=## 4\.)', spec_content, re.DOTALL)
    sections["section_3"] = match.group(1).strip() if match else ""
    
    # Extract Section 4.1
    match = re.search(r'### 4\.1[^#]+(.*?)(?=### 4\.2)', spec_content, re.DOTALL)
    sections["section_4_1"] = match.group(1).strip() if match else ""
    
    # Extract Section 4.2
    match = re.search(r'### 4\.2[^#]+(.*?)(?=### 4\.3)', spec_content, re.DOTALL)
    sections["section_4_2"] = match.group(1).strip() if match else ""
    
    # Extract Section 4.3
    match = re.search(r'### 4\.3[^#]+(.*?)(?=$|\Z)', spec_content, re.DOTALL)
    sections["section_4_3"] = match.group(1).strip() if match else ""
    
    return sections
```

### 3.6 Compliance Validator Tool

```python
import ast
import re

@tool
def validate_10_2_compliance(code_str: str, yaml_str: str) -> Dict[str, Any]:
    """
    Three-layer validator: AST static check + Runtime sandbox + Dual artifact consistency check
    
    Implemented based on Plan_v2.txt Gate 1/2 requirements.
    
    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "gate_results": {
                "gate1_signature": bool,
                "gate1_schema": bool,
                "gate1_type_safety": bool,
                "gate2_none_safety": bool,
                "gate2_alternatives": bool,
                "gate2_bad_regex": bool,
                "gate2_precedence": bool,
                "consistency": bool
            }
        }
    """
    errors = []
    gate_results = {}

    # === Level 1: AST Static Safety Check (Plan_v2.txt L14, L405-427) ===
    try:
        tree = ast.parse(code_str)
        
        # Check forbidden IO operations
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['open', 'read', 'write', 'print', 'eval', 'exec']:
                    errors.append(f"CRITICAL [Gate1]: Forbidden IO function '{node.func.id}' detected.")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name in ['os', 'sys', 'subprocess', 'pathlib']:
                        errors.append(f"CRITICAL [Gate1]: Forbidden import '{alias.name}' detected.")
        
        # Check function signatures
        func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        
        gate_results["gate1_signature"] = all(name in func_names for name in ['extract_context', 'validate_logic', 'check_existence'])
        if not gate_results["gate1_signature"]:
            errors.append("FAIL [Gate1]: Missing required function(s). Need: extract_context, validate_logic, check_existence")
        
    except SyntaxError as e:
        return {"valid": False, "errors": [f"Syntax Error: {e}"], "gate_results": {}}

    if any("CRITICAL" in e for e in errors):
        return {"valid": False, "errors": errors, "gate_results": gate_results}

    # === Level 2: Runtime Sandbox Test (Plan_v2.txt L431-452) ===
    local_scope = {}
    try:
        exec(code_str, {"re": re, "fnmatch": __import__('fnmatch')}, local_scope)
        
        # Gate 1: Type Lock Test
        if 'extract_context' in local_scope:
            func = local_scope['extract_context']
            mock_result = func("Test line with value 123", "test.log")
            
            gate_results["gate1_schema"] = isinstance(mock_result, list)
            if mock_result and len(mock_result) > 0:
                item = mock_result[0]
                gate_results["gate1_type_safety"] = isinstance(item.get('value'), str)
                if not gate_results["gate1_type_safety"]:
                    errors.append(f"FAIL [Gate1]: 'value' is {type(item.get('value'))}, MUST be str")
                
                required_keys = {'value', 'source_file', 'line_number', 'matched_content', 'parsed_fields'}
                missing_keys = required_keys - set(item.keys())
                if missing_keys:
                    errors.append(f"FAIL [Gate1]: Missing keys in ParsedItem: {missing_keys}")
        
        # Gate 2: Atom B Test Vectors
        if 'validate_logic' in local_scope:
            func = local_scope['validate_logic']
            
            # Test 1: None-Safety (Plan_v2.txt L433)
            try:
                func("abc", "a", parsed_fields=None)
                gate_results["gate2_none_safety"] = True
            except:
                gate_results["gate2_none_safety"] = False
                errors.append("FAIL [Gate2]: None-Safety test failed")
            
            # Test 2: Empty Alternatives (Plan_v2.txt L436)
            res = func("abc", "|a||")
            gate_results["gate2_alternatives"] = res.get('is_match') == True and res.get('kind') == 'alternatives'
            if not gate_results["gate2_alternatives"]:
                errors.append("FAIL [Gate2]: Empty Alternatives test failed")
            
            # Test 3: Bad Regex (Plan_v2.txt L439)
            res = func("abc", "regex:[", regex_mode="search")
            gate_results["gate2_bad_regex"] = res.get('is_match') == False and 'Invalid' in res.get('reason', '')
            if not gate_results["gate2_bad_regex"]:
                errors.append("FAIL [Gate2]: Bad Regex handling test failed")
            
            # Test 5: Wildcard Priority (Plan_v2.txt L447)
            res = func("abc", "a*c")
            gate_results["gate2_precedence"] = res.get('kind') == 'wildcard'
            if not gate_results["gate2_precedence"]:
                errors.append("FAIL [Gate2]: Wildcard precedence test failed")
            
            # Test 4: Literal Alternatives (Plan_v2.txt L442-443)
            # "regex:^a" should be treated as literal inside alternatives
            res_literal = func("regex:^a", "regex:^a|zzz")
            gate_results["gate2_literal_alt"] = res_literal.get('is_match') == True
            if not gate_results["gate2_literal_alt"]:
                errors.append("FAIL [Gate2]: Literal Alternatives test failed - 'regex:^a' should match as literal")
            
            # Test 6: Default Strategy Policy (Plan_v2.txt L449-450)
            res_contains = func("abc", "b", default_match="contains")
            res_exact = func("abc", "b", default_match="exact")
            gate_results["gate2_default_strategy"] = (
                res_contains.get('is_match') == True and 
                res_contains.get('kind') == 'contains' and
                res_exact.get('is_match') == False and
                res_exact.get('kind') == 'exact'
            )
            if not gate_results["gate2_default_strategy"]:
                errors.append("FAIL [Gate2]: Default Strategy Policy test failed")
            
            # Test 7: regex_mode Invalid Value (Plan_v2.txt L452)
            # Invalid regex_mode should default to 'search' behavior, not raise
            try:
                res_bad_mode = func("abc", "regex:^a", regex_mode="INVALID_MODE")
                gate_results["gate2_invalid_mode"] = res_bad_mode.get('is_match') == True
                if not gate_results["gate2_invalid_mode"]:
                    errors.append("FAIL [Gate2]: Invalid regex_mode should default to search")
            except Exception:
                gate_results["gate2_invalid_mode"] = False
                errors.append("FAIL [Gate2]: Invalid regex_mode raised exception instead of defaulting to search")
        
        # Gate 1: Atom C evidence field (Plan_v2.txt L157)
        if 'check_existence' in local_scope:
            func = local_scope['check_existence']
            evidence = [{'value': 'test'}]
            res = func(evidence)
            if res.get('evidence') != evidence:
                errors.append("FAIL [Gate1]: Atom C failed to pass through 'evidence' list")

    except Exception as e:
        errors.append(f"Runtime Error: {str(e)}")

    # === Level 3: Dual Artifact Consistency Check ===
    if "regex:" in yaml_str and "re." not in code_str and "regex" not in code_str.lower():
        errors.append("Consistency Error: YAML specifies regex pattern, but code lacks regex handling")
        gate_results["consistency"] = False
    else:
        gate_results["consistency"] = True

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "gate_results": gate_results
    }
```

---

## 4. Prompt Templates

### 4.1 Agent A System Prompt (Parsing Expert)

**Input Scope**: Section 1 (Parsing Logic) + Section 4.1 (Implementation Guide) + Tools

```markdown
# Role
You are the **Parsing Expert Agent** for "Hierarchical Checker Architecture 10.2".
Your task is to write the `extract_context` Python function (Atom A).

# 10.2 Architecture Constraints (NON-NEGOTIABLE)
1. **Pure Function**: NO `open()`, `read()`, `print()`, or file I/O. You process the `text` string argument only.
2. **Type Hard Lock**: The `value` key in output MUST be `str`. Use `str()` conversion explicitly.
3. **PR5**: Do NOT filter results. Extract EVERYTHING that matches the patterns.
4. **Signature**: `def extract_context(text: str, source_file: str) -> List[Dict]`
5. **Output Schema**: Each dict MUST have exactly these keys:
   - `value`: (str) Primary string for matching
   - `source_file`: (str) Passed from input
   - `line_number`: (int) Line where match occurred
   - `matched_content`: (str) Raw line text
   - `parsed_fields`: (dict) Detailed metadata as specified in ItemSpec

# Standardization Layer (MUST INCLUDE)
After your extraction logic, you MUST include this exact code block:
```python
# [Locked] Standardization Layer
standardized_output = []
for item in results:
    safe_value = str(item.get("value", ""))
    standardized_item = {
        "value": safe_value,
        "source_file": source_file,
        "line_number": item.get("line_number"),
        "matched_content": str(item.get("matched_content", "")),
        "parsed_fields": item.get("parsed_fields", {})
    }
    standardized_output.append(standardized_item)
return standardized_output
```

# ItemSpec GUIDANCE (Section 1 + 4.1 ONLY)
The following is GUIDANCE only. You MUST adapt based on ACTUAL log content you observe.
- Section 1 describes WHAT fields to extract
- Section 4.1 describes WHERE to find data and HOW to extract it

{itemspec_section_1}

{itemspec_section_4_1}

# Available Tools
You have access to tools for reading log files. Use them wisely:
1. `list_available_files(patterns)` - First, discover what files exist
2. `read_file_header(file, max_lines)` - Read file header for version info
3. `search_in_file(file, keywords)` - Search for relevant content
4. `read_file_range(file, start, end)` - Read specific line range if needed

**Tool Constraints**:
- You MUST call `list_available_files` before reading any file
- Single read limited to 200 lines max
- Use `search_in_file` to find relevant sections, don't read entire files

# CRITICAL: Autonomous Adaptation
- ItemSpec is GUIDANCE, not a strict template
- You MUST adapt your parsing strategy based on ACTUAL observed log content
- If you discover references to other files (e.g., SPEF path in STA log), you MAY call tools to read those files
- If actual log format differs from ItemSpec examples, follow the ACTUAL format

# Your Workflow
1. Call `list_available_files` to see available logs
2. Call `read_file_header` or `search_in_file` to examine content
3. Based on ACTUAL content, decide what to extract
4. If nested files are referenced, call tools to read them
5. Write `extract_context` function that handles the ACTUAL format

# Output Format
Provide ONLY the Python function code. No explanations outside code comments.
```

### 4.2 Agent B System Prompt (Logic Expert)

**Input Scope**: Section 2 (Check Logic) + Section 3 (Waiver Logic) + Section 4.2 (Special Scenarios) + Agent A Code + YAML Template

**Section Delivery Strategy**: In LangGraph mode, ALL sections (2 + 3 + 4.2) are provided to Agent B in a **single prompt**. This ensures:
- Complete context for understanding validation items and their waiver relationships
- Consistent interpretation of check logic and waiver scenarios
- No information loss between sections due to context fragmentation

```markdown
# Role
You are the **Logic Developer Agent** for "Hierarchical Checker Architecture 10.2".
Your task is to write universal Atom B (validate_logic) and Atom C (check_existence) functions, plus a YAML configuration.

# 10.2 Architecture Constraints (NON-NEGOTIABLE)

## Atom B: validate_logic
1. **Signature**: `def validate_logic(text, pattern, parsed_fields=None, default_match="contains", regex_mode="search")`
2. **Hard Precedence Rules** (MUST implement in this order):
   - Priority 1: Alternatives (if `|` in pattern) → Split and check ANY segment
   - Priority 2: Regex (if pattern starts with `regex:`) → Use re.search or re.match based on regex_mode
   - Priority 3: Wildcard (if `*` or `?` in pattern) → Use fnmatch.fnmatchcase
   - Priority 4: Default → String containment or equality based on default_match
3. **Return Schema**: `{'is_match': bool, 'reason': str, 'kind': str}`
   - 'kind' values: "alternatives", "regex", "wildcard", "contains", "exact"
4. **Safety**: Catch `re.error` and return `is_match=False` with reason starting with "Invalid Regex:"

## Atom C: check_existence
1. **Signature**: `def check_existence(items: List[Dict]) -> Dict`
2. **Return Schema**: `{'is_match': bool, 'reason': str, 'evidence': items}`
3. **Logic**: Return is_match=True if items list is non-empty

# CRITICAL: Zero Hardcoding Policy
- Your Python code must be UNIVERSAL
- Do NOT include any item-specific keywords like tool names, file patterns, or version numbers
- All business logic is driven by the YAML configuration, not hardcoded in Python

# ItemSpec CONTEXT (Section 2 + 3 + 4.2)
{itemspec_section_2}

{itemspec_section_3}

{itemspec_section_4_2}

# Agent A Code Reference
This is the `extract_context` function that Agent A generated. Study the `parsed_fields` structure.
```python
{agent_a_code}
```

# YAML Template
Fill in the values based on ItemSpec requirements. You know these fields exist:
```yaml
# === YAML Configuration Template ===
requirements:
  value: <TO_BE_INFERRED>        # N/A or integer count
  pattern_items: <TO_BE_INFERRED> # List of patterns (can use |, regex:, *, ?)
waivers:
  value: <TO_BE_INFERRED>        # N/A, 0 (global), or integer count
  waive_items: <TO_BE_INFERRED>  # List of waiver keywords
  waive_reasons: <TO_BE_INFERRED> # Corresponding reasons
```

# Your Task
1. Write UNIVERSAL Atom B and Atom C code (same code works for ALL items)
2. Infer appropriate values for the YAML configuration based on ItemSpec
3. Ensure the YAML pattern_items and waive_items align with ItemSpec definitions

# Output Format
```python
# === ATOM B ===
def validate_logic(...):
    ...

# === ATOM C ===
def check_existence(...):
    ...
```

```yaml
# === YAML Configuration for {item_id} ===
requirements:
  value: ...
  pattern_items: [...]
waivers:
  value: ...
  waive_items: [...]
```
```

### 4.3 Reflect Node Prompt

```markdown
# Context
Your previous code generation attempt FAILED validation.

# Error Details
{validation_errors}

# Gate Results
{gate_results}

# Your Previous Code
{previous_code}

# Instructions
1. Analyze each error message carefully
2. Identify the root cause (missing key, wrong type, logic error, etc.)
3. Fix ONLY the issues identified - do not rewrite unrelated code
4. Ensure all 10.2 constraints are still satisfied after fixes

# Output
Provide the corrected Python code only.
```

---

## 5. Failure Handling and Human Intervention

### 5.1 Safe Stub and Error Report

```python
def generate_human_intervention_report(state: AgentState) -> Dict[str, Any]:
    """
    Generate human intervention report when iteration_count >= 3.
    
    Returns:
        {
            "status": "HUMAN_INTERVENTION_REQUIRED",
            "item_id": "...",
            "failure_summary": "...",
            "error_history": [...],
            "last_generated_code": "...",
            "suggested_actions": [...]
        }
    """
    report = {
        "status": "HUMAN_INTERVENTION_REQUIRED",
        "item_id": state.get("item_spec_path", "unknown"),
        "total_iterations": state["iteration_count"],
        "failure_summary": f"Failed to generate compliant code after {state['iteration_count']} attempts",
        "error_history": state.get("error_history", []),
        "last_validation_errors": state.get("validation_errors", []),
        "last_generated_code": {
            "atom_a": state.get("atom_a_code", ""),
            "atom_b": state.get("atom_b_code", ""),
            "atom_c": state.get("atom_c_code", ""),
            "yaml": state.get("yaml_config", "")
        },
        "suggested_actions": [
            "Review the ItemSpec for ambiguous requirements",
            "Check if the log snippet format matches ItemSpec expectations",
            "Manually verify the extraction patterns in ItemSpec Section 4.1",
            "Consider simplifying the parsing logic for this item"
        ],
        "cache_location": f"./cache/{state.get('item_spec_path', 'unknown').replace('.md', '')}/",
        "resume_command": f"python agent.py --resume --item {state.get('item_spec_path', '')}"
    }
    
    return report


def handle_max_iterations(state: AgentState, cache: StateCache) -> AgentState:
    """Handle the case when max iteration count is reached"""
    
    # Generate human intervention report
    report = generate_human_intervention_report(state)
    
    # Save report to cache
    item_id = state.get("item_spec_path", "unknown").replace(".md", "")
    cache.save_stage_output(item_id, "human_intervention_report", report)
    
    # Update state
    state["current_stage"] = "human_required"
    cache.save_checkpoint(item_id, state)
    
    # Print report summary
    print("\n" + "="*60)
    print("⚠️  HUMAN INTERVENTION REQUIRED")
    print("="*60)
    print(f"Item: {report['item_id']}")
    print(f"Iterations: {report['total_iterations']}")
    print(f"Last Errors: {report['last_validation_errors'][:3]}...")
    print(f"Report saved to: {report['cache_location']}")
    print(f"Resume with: {report['resume_command']}")
    print("="*60 + "\n")
    
    return state
```

### 5.2 Conditional Edge Logic (Smart Repair Routing)

```python
def should_continue(state: AgentState) -> str:
    """
    Conditional edge decision: determine which node to go next.
    
    Smart repair strategy:
    - If error source is Atom A -> Only rerun Agent A, keep Agent B cache
    - If error source is Atom B/C/YAML -> Only rerun Agent B, reuse Agent A result
    
    Returns:
        "done" | "reflect_a" | "reflect_b" | "human_required"
    """
    if not state.get("validation_errors"):
        return "done"
    
    if state["iteration_count"] >= 3:
        return "human_required"
    
    # Smart error source detection, decide which Agent to repair
    error_source = determine_error_source(state)
    state["error_source"] = error_source
    
    if error_source == "atom_a":
        return "reflect_a"
    else:
        return "reflect_b"


def determine_error_source(state: AgentState) -> str:
    """
    Analyze validation errors, determine which Atom caused the error.
    
    Decision rules:
    - Contains "extract_context", "ParsedItem", "value", "parsed_fields" -> atom_a
    - Contains "validate_logic", "kind", "precedence", "regex_mode" -> atom_b  
    - Contains "check_existence", "evidence" -> atom_c
    - Contains "YAML", "Consistency" -> yaml
    - Other cases -> unknown (default to rerunning Agent A)
    """
    errors = state.get("validation_errors", [])
    error_text = " ".join(errors).lower()
    
    # Atom A related error keywords
    atom_a_keywords = [
        "extract_context", "parseditem", "atom a",
        "missing keys", "source_file", "line_number", 
        "matched_content", "type(item.get('value'))"
    ]
    
    # Atom B related error keywords
    atom_b_keywords = [
        "validate_logic", "atom b", "kind", "precedence",
        "alternatives", "regex_mode", "wildcard", "gate2"
    ]
    
    # Atom C related error keywords
    atom_c_keywords = [
        "check_existence", "atom c", "evidence"
    ]
    
    # YAML related error keywords
    yaml_keywords = [
        "yaml", "consistency", "pattern_items", "waive_items"
    ]
    
    # Check by priority
    if any(kw in error_text for kw in atom_a_keywords):
        return "atom_a"
    elif any(kw in error_text for kw in atom_b_keywords):
        return "atom_b"
    elif any(kw in error_text for kw in atom_c_keywords):
        return "atom_c"
    elif any(kw in error_text for kw in yaml_keywords):
        return "yaml"
    else:
        return "unknown"  # Default to Atom A issue


def reflect_a_node(state: AgentState) -> AgentState:
    """
    Reflect Node for Atom A:
    Only fix extract_context, keep Agent B cached results.
    """
    state["iteration_count"] += 1
    state["current_stage"] = "reflect_a"
    
    # Record error history
    state["error_history"].append({
        "iteration": state["iteration_count"],
        "errors": state["validation_errors"],
        "source": "atom_a",
        "timestamp": datetime.now().isoformat()
    })
    
    # Call LLM to fix Atom A
    # ... (using Reflect Prompt + previous atom_a_code)
    
    return state


def reflect_b_node(state: AgentState) -> AgentState:
    """
    Reflect Node for Atom B/C/YAML:
    Only fix validate_logic/check_existence/YAML, reuse Agent A result.
    """
    state["iteration_count"] += 1
    state["current_stage"] = "reflect_b"
    
    # Record error history
    state["error_history"].append({
        "iteration": state["iteration_count"],
        "errors": state["validation_errors"],
        "source": state.get("error_source", "atom_b"),
        "timestamp": datetime.now().isoformat()
    })
    
    # Call LLM to fix Atom B/C/YAML
    # ... (using Reflect Prompt + previous atom_b_code/atom_c_code/yaml_config)
    
    return state


# ============================================================
# Section 5.3: Core Node Function Implementation
# ============================================================

def load_spec_node(state: AgentState) -> AgentState:
    """
    Load and parse ItemSpec file, separate each Section.
    
    Input:
        - state["item_spec_path"]: ItemSpec file path
    
    Output:
        - state["item_spec_content"]: Raw content
        - state["spec_sections"]: Separated Section contents
    """
    state["current_stage"] = "load_spec"
    
    # Load ItemSpec file
    config = AgentConfig.load()
    spec_path = os.path.join(config.item_specs_dir, state["item_spec_path"])
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        state["item_spec_content"] = f.read()
    
    # Separate each Section (for information isolation)
    state["spec_sections"] = extract_itemspec_sections(state["item_spec_content"])
    
    state["updated_at"] = datetime.now().isoformat()
    return state


def preprocess_node(state: AgentState) -> AgentState:
    """
    Framework preprocessing node: resolve path variables, initialize tool constraints.
    
    This node executes automatically before Agent runs, invisible to LLM.
    
    Functions:
        - Resolve path variables like ${CHECKLIST_ROOT}
        - Initialize Tool quota counters
        - Prepare available file list
    """
    state["current_stage"] = "preprocess"
    
    config = AgentConfig.load()
    
    # Path variable resolution
    env_vars = {
        "CHECKLIST_ROOT": config.search_root,
        "DESIGN_ROOT": config.search_root,
        "LOG_ROOT": os.path.join(config.search_root, "logs")
    }
    state["resolved_env_vars"] = env_vars
    
    # Initialize Tool quota
    state["tool_quota"] = {
        "bytes_read": 0,
        "max_bytes": 100 * 1024,  # 100KB
        "files_discovered": 0,
        "max_files": 20
    }
    
    state["updated_at"] = datetime.now().isoformat()
    return state


def agent_a_node(state: AgentState) -> AgentState:
    """
    Agent A: Generate Atom A (extract_context)
    
    Input Scope (Information Isolation):
        - Section 1 (Parsing Logic)
        - Section 4.1 (Data Source & Extraction)
        - Tools (constrained)
    
    Forbidden:
        - Section 2 (Check Logic)
        - Section 3 (Waiver Logic)
        - Actual values of pattern_items / requirements.value
    
    Output:
        - state["atom_a_code"]: extract_context function code
        - state["atom_a_reasoning"]: Reasoning process
    """
    state["current_stage"] = "agent_a"
    
    config = AgentConfig.load()
    client, params = get_llm_client(config.agent_a_llm)
    
    # Build Agent A Prompt (only Section 1 + 4.1)
    prompt = build_agent_a_prompt(
        section_1=state["spec_sections"]["section_1"],
        section_4_1=state["spec_sections"]["section_4_1"],
        resolved_paths=state.get("resolved_env_vars", {})
    )
    
    # Bind Tools (constrained)
    tools = [
        list_available_files,
        read_file_header,
        search_in_file,
        read_file_range
    ]
    
    # Call LLM with Tools
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        tools=format_tools_for_llm(tools),
        **params
    )
    
    # Handle Tool Calls (if any)
    final_response = handle_tool_calls(response, tools, state, client, params)
    
    # Parse response
    atom_a_code, reasoning = parse_agent_response(final_response)
    
    state["atom_a_code"] = atom_a_code
    state["atom_a_reasoning"] = reasoning
    state["updated_at"] = datetime.now().isoformat()
    return state


def agent_b_node(state: AgentState) -> AgentState:
    """
    Agent B: Generate Atom B, C and YAML configuration
    
    Input Scope (Information Isolation):
        - Section 2 (Check Logic)
        - Section 3 (Waiver Logic)
        - Section 4.2 (Special Scenarios)
        - Agent A generated code
        - YAML empty template
    
    Forbidden:
        - Section 1 (Parsing Logic)
        - Section 4.1 (Data Source)
        - Raw log content
    
    Output:
        - state["atom_b_code"]: validate_logic function code
        - state["atom_c_code"]: check_existence function code
        - state["yaml_config"]: YAML configuration
        - state["atom_b_reasoning"]: Reasoning process
    """
    state["current_stage"] = "agent_b"
    
    config = AgentConfig.load()
    client, params = get_llm_client(config.agent_b_llm)
    
    # Build Agent B Prompt (only Section 2 + 3 + 4.2)
    prompt = build_agent_b_prompt(
        section_2=state["spec_sections"]["section_2"],
        section_3=state["spec_sections"]["section_3"],
        section_4_2=state["spec_sections"]["section_4_2"],
        agent_a_code=state["atom_a_code"],
        yaml_template=YAML_TEMPLATE
    )
    
    # Call LLM (Agent B does not need Tools)
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        **params
    )
    
    # Parse response
    atom_b_code, atom_c_code, yaml_config, reasoning = parse_agent_b_response(
        response.choices[0].message.content
    )
    
    state["atom_b_code"] = atom_b_code
    state["atom_c_code"] = atom_c_code
    state["yaml_config"] = yaml_config
    state["atom_b_reasoning"] = reasoning
    state["updated_at"] = datetime.now().isoformat()
    return state


# YAML Empty Template Constant
YAML_TEMPLATE = """
# === YAML Configuration Template ===
# Agent B: Infer the following values based on ItemSpec
requirements:
  value: <TO_BE_INFERRED>        # N/A (Type 1/4) or integer (Type 2/3)
  pattern_items: <TO_BE_INFERRED> # List of patterns
waivers:
  value: <TO_BE_INFERRED>        # N/A (Type 1/2), 0 (global), or integer (selective)
  waive_items: <TO_BE_INFERRED>  # List of waiver keywords
  waive_reasons: <TO_BE_INFERRED> # Corresponding reasons
"""

# ============================================================
# YAML Field Semantics Reference (Key Information)
# ============================================================
#
# --- Checker Type System (4 Types) ---
# | Type   | Pattern Search | Waiver Support | requirements.value | waivers.value |
# |--------|----------------|----------------|--------------------|--------------|
# | Type 1 | No             | No             | N/A                | N/A          |
# | Type 2 | Yes            | No             | integer (>0)       | N/A          |
# | Type 3 | Yes            | Yes            | integer (>0)       | 0 or >0      |
# | Type 4 | No             | Yes            | N/A                | 0 or >0      |
#
# --- requirements.value Semantics ---
# - N/A: Type 1/4, no pattern search (boolean check only)
# - Integer (>0): Type 2/3, count of pattern_items list
#
# --- requirements.pattern_items Format ---
# - Contains Match (Default): "2025" -> checks if "2025" in item.value
# - Wildcard Match: "*Genus*" -> fnmatch(item.value, "*Genus*")
# - Regex Match: "regex:\d{4}" -> re.search("\d{4}", item.value)
# - Alternatives: "2025|Genus" -> split by |, any one match is sufficient
#
# --- waivers.value Semantics ---
# - N/A: Type 1/2, no waiver support
# - 0: Global waiver mode, all violations -> INFO, auto PASS
# - >0: Selective waiver mode, count of waive_items patterns
#
# --- waivers.waive_items Behavior ---
# - When value=0: Contains comments/reasons (informational)
# - When value>0: Contains actual waiver patterns (same format as pattern_items)
#
# --- Waiver Matching Strategies (Selective Mode) ---
# - Exact Match: pattern == item
# - Wildcard Match: fnmatch(item, pattern)
# - Regex Match: re.match(pattern.removeprefix("regex:"), item)
# ============================================================


def validate_node(state: AgentState) -> AgentState:
    """
    Validation Node: Call three-layer validator.
    
    Validation Content:
        - Gate 1: AST static check
        - Gate 2: Runtime sandbox test
        - Gate 3: Dual artifact consistency
    
    Output:
        - state["validation_errors"]: Error list
        - state["gate_results"]: Each Gate result
        - state["error_source"]: Error source determination
    """
    state["current_stage"] = "validate"
    
    # Merge all code
    full_code = f'''
{state["atom_a_code"]}

{state["atom_b_code"]}

{state["atom_c_code"]}
'''
    
    # Call validator
    validation_result = validate_10_2_compliance(full_code, state["yaml_config"])
    
    state["validation_errors"] = validation_result.get("errors", [])
    state["gate_results"] = validation_result.get("gate_results", {})
    
    # If errors exist, determine error source
    if state["validation_errors"]:
        state["error_source"] = determine_error_source(state)
    else:
        state["error_source"] = ""
    
    state["updated_at"] = datetime.now().isoformat()
    return state


def human_required_node(state: AgentState) -> AgentState:
    """
    Human Intervention Node: Generate report and stop execution.
    """
    state["current_stage"] = "human_required"
    
    # Generate human intervention report
    report = generate_human_intervention_report(state)
    
    # Save report
    cache = FileSystemCache()
    item_id = generate_item_id(state["item_spec_path"])
    cache.save_stage_output(item_id, "human_intervention_report", report)
    
    state["updated_at"] = datetime.now().isoformat()
    return state


# ============================================================
# Section 5.4: Helper Functions
# ============================================================

def build_agent_a_prompt(section_1: str, section_4_1: str, resolved_paths: Dict) -> str:
    """
    Build Agent A Prompt.
    
    Information isolation: only includes Section 1 + 4.1
    """
    return AGENT_A_PROMPT_TEMPLATE.format(
        itemspec_section_1=section_1,
        itemspec_section_4_1=section_4_1,
        resolved_paths=json.dumps(resolved_paths, indent=2)
    )


def build_agent_b_prompt(section_2: str, section_3: str, section_4_2: str, 
                          agent_a_code: str, yaml_template: str) -> str:
    """
    Build Agent B Prompt.
    
    Information isolation: only includes Section 2 + 3 + 4.2 + Agent A Code + YAML Template
    """
    return AGENT_B_PROMPT_TEMPLATE.format(
        itemspec_section_2=section_2,
        itemspec_section_3=section_3,
        itemspec_section_4_2=section_4_2,
        agent_a_code=agent_a_code,
        yaml_template=yaml_template
    )


def format_tools_for_llm(tools: List) -> List[Dict]:
    """Format Python functions to LLM Tool format"""
    formatted = []
    for tool in tools:
        formatted.append({
            "type": "function",
            "function": {
                "name": tool.__name__,
                "description": tool.__doc__,
                "parameters": extract_function_parameters(tool)
            }
        })
    return formatted


def handle_tool_calls(response, tools: List, state: AgentState, client, params: Dict) -> str:
    """
    Handle LLM Tool Calls, execute tools and return final response.
    
    Includes quota check and constraint validation.
    """
    tool_map = {tool.__name__: tool for tool in tools}
    messages = []
    
    while response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # Quota check
            if not check_tool_quota(state, tool_name, tool_args):
                result = {"error": "Tool quota exceeded"}
            else:
                # Execute tool
                result = tool_map[tool_name](**tool_args)
                update_tool_quota(state, result)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })
        
        # Continue conversation
        response = client.chat.completions.create(
            messages=messages,
            tools=format_tools_for_llm(tools),
            **params
        )
    
    return response.choices[0].message.content


def check_tool_quota(state: AgentState, tool_name: str, args: Dict) -> bool:
    """Check if Tool call exceeds quota"""
    quota = state.get("tool_quota", {})
    
    if quota.get("bytes_read", 0) >= quota.get("max_bytes", 100*1024):
        return False
    
    if tool_name in ["read_file_range", "read_file_header", "search_in_file"]:
        if "require_discovery_before_read" in quota and not state.get("files_discovered"):
            return False
    
    return True


def update_tool_quota(state: AgentState, result: Dict) -> None:
    """Update Tool quota counter"""
    if "content" in result:
        state["tool_quota"]["bytes_read"] += len(result["content"])
    if "files" in result:
        state["tool_quota"]["files_discovered"] = True


def parse_agent_response(response: str) -> Tuple[str, str]:
    """Parse Agent response, extract code and reasoning"""
    # Extract code block
    code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
    code = code_match.group(1) if code_match else response
    
    # Extract reasoning (content outside code block)
    reasoning = re.sub(r'```python\n.*?```', '', response, flags=re.DOTALL).strip()
    
    return code, reasoning


def parse_agent_b_response(response: str) -> Tuple[str, str, str, str]:
    """Parse Agent B response, extract Atom B, C, YAML and reasoning"""
    # Extract multiple code blocks
    code_blocks = re.findall(r'```(?:python|yaml)\n(.*?)```', response, re.DOTALL)
    
    atom_b_code = ""
    atom_c_code = ""
    yaml_config = ""
    
    for block in code_blocks:
        if 'def validate_logic' in block:
            atom_b_code = block
        elif 'def check_existence' in block:
            atom_c_code = block
        elif 'requirements:' in block or 'waivers:' in block:
            yaml_config = block
    
    reasoning = re.sub(r'```(?:python|yaml)\n.*?```', '', response, flags=re.DOTALL).strip()
    
    return atom_b_code, atom_c_code, yaml_config, reasoning


def generate_item_id(item_spec_path: str) -> str:
    """Generate unique item_id from ItemSpec path"""
    # Unified item_id generation logic
    base_name = os.path.basename(item_spec_path)
    return base_name.replace("_ItemSpec.md", "").replace(".md", "").replace("/", "_").replace("\\\\", "_")


def create_initial_state(item_spec_path: str, search_root: str = "") -> AgentState:
    """
    Create initial AgentState for a new run.
    
    Args:
        item_spec_path: Path to ItemSpec file
        search_root: Root directory for log file search
    
    Returns:
        Initialized AgentState dictionary
    """
    from datetime import datetime
    
    return {
        "item_spec_path": item_spec_path,
        "item_spec_content": "",
        "discovered_log_files": [],
        "log_snippets": {},
        "atom_a_code": "",
        "atom_a_reasoning": "",
        "atom_b_code": "",
        "atom_c_code": "",
        "yaml_config": "",
        "atom_b_reasoning": "",
        "validation_errors": [],
        "gate_results": {},
        "error_source": "",
        "current_stage": "init",
        "iteration_count": 0,
        "checkpoint_id": "",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "error_history": [],
        "spec_sections": {},
        "resolved_env_vars": {},
        "tool_quota": {},
        # Multi-turn Context Maintenance
        "conversation_summary": "",
        "generated_code_signatures": {},
        "key_decisions": [],
        "iteration_context": {}
    }


def extract_function_parameters(func) -> Dict[str, Any]:
    """
    Extract function parameters for LLM tool format.
    
    Uses function annotations and docstring to build JSON schema.
    """
    import inspect
    
    sig = inspect.signature(func)
    params = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for name, param in sig.parameters.items():
        param_type = "string"  # default
        if param.annotation != inspect.Parameter.empty:
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == List[str]:
                param_type = "array"
        
        params["properties"][name] = {"type": param_type}
        
        if param.default == inspect.Parameter.empty:
            params["required"].append(name)
    
    return params
```

---

## 6. Complete Execution Flow

### 6.1 Main Entry

```python
from langgraph.graph import StateGraph, END

def build_agent_graph() -> StateGraph:
    """Build LangGraph workflow (supports smart repair routing)"""
    
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("load_spec", load_spec_node)
    graph.add_node("preprocess", preprocess_node)   # New: Framework preprocessing
    graph.add_node("agent_a", agent_a_node)         # Agent A with Tools
    graph.add_node("agent_b", agent_b_node)
    graph.add_node("validate", validate_node)
    graph.add_node("reflect_a", reflect_a_node)
    graph.add_node("reflect_b", reflect_b_node)
    graph.add_node("human_required", human_required_node)
    
    # Add edges: Normal flow (updated)
    graph.add_edge("load_spec", "preprocess")      # New preprocessing step
    graph.add_edge("preprocess", "agent_a")        # After preprocess enter Agent A
    graph.add_edge("agent_a", "agent_b")
    graph.add_edge("agent_b", "validate")
    
    # Conditional edges: Smart repair routing
    graph.add_conditional_edges(
        "validate",
        should_continue,
        {
            "done": END,
            "reflect_a": "reflect_a",      # Atom A error
            "reflect_b": "reflect_b",      # Atom B/C/YAML error
            "human_required": "human_required"
        }
    )
    
    # Smart repair: Decide which Agent to return to based on error source
    graph.add_edge("reflect_a", "agent_a")   # Atom A error -> Rerun Agent A -> Agent B -> Validate
    graph.add_edge("reflect_b", "agent_b")   # Atom B/C/YAML error -> Only rerun Agent B -> Validate
    graph.add_edge("human_required", END)
    
    # Set entry point
    graph.set_entry_point("load_spec")
    
    return graph.compile()


def run_agent(item_spec_path: str, search_root: str, resume: bool = False):
    """
    Run Agent main entry.
    
    Args:
        item_spec_path: ItemSpec file path
        search_root: Log file search root directory
        resume: Whether to resume from checkpoint
    """
    cache = FileSystemCache("./cache")
    item_id = item_spec_path.replace(".md", "").replace("/", "_")
    
    # Checkpoint recovery or initialization
    if resume:
        state = resume_from_checkpoint(item_id, cache)
        if state["current_stage"] in ("done", "human_required"):
            print(f"[INFO] Cannot resume from stage: {state['current_stage']}")
            return state
    else:
        state = create_initial_state(item_spec_path, search_root)
    
    # Build and run graph
    graph = build_agent_graph()
    
    # Stream execution (supports real-time state updates)
    for event in graph.stream(state):
        node_name = list(event.keys())[0]
        node_state = event[node_name]
        
        # Save checkpoint after each node completes
        cache.save_checkpoint(item_id, node_state)
        cache.save_stage_output(item_id, node_name, {
            "timestamp": datetime.now().isoformat(),
            "outputs": extract_stage_outputs(node_name, node_state)
        })
        
        print(f"[{node_state['current_stage']}] Completed. Iteration: {node_state['iteration_count']}")
    
    return node_state
```

---

## 7. Design Decision Records

The following decisions have been confirmed and integrated into the document:

| Decision Point | Choice | Implementation Location |
|--------|------|----------|
| **Log Search Scope** | Config file | Section 1.4 `agent_config.yaml` -> `paths.search_root` |
| **LLM Model Selection** | Configurable | Section 1.4 `agent_config.yaml` -> `llm.agent_a/agent_b/reflect` |
| **Cache Cleanup Policy** | Save by hour | Section 2.1 hourly directory structure + Section 2.2 `_cleanup_hourly_checkpoints()` |
| **Reflect Repair Granularity** | Only fix errored part | Section 5.2 smart routing `determine_error_source()` + `reflect_a/b_node()` |
| **Agent A Input Scope** | Section 1 + 4.1 only | Section 1.5 information isolation + Section 4.1 Prompt |
| **Agent B Input Scope** | Section 2 + 3 + 4.2 | Section 1.5 information isolation + Section 4.2 Prompt |
| **Tool Call Mode** | LLM active call, framework constrained | Section 3.0 Tool call constraint mechanism |
| **Path Variable Handling** | Framework preprocessing (invisible to LLM) | Section 3.0.3 `resolve_path_variables()` |
| **YAML Template Exposure** | Empty template to Agent B | Section 4.2 Prompt + `YAML_TEMPLATE` |

### 7.1 Architecture Overview Diagram (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agent Orchestrator                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ Load     │───▶│Preprocess│───▶│  Agent A │───▶│  Agent B │             │
│   │ Spec     │    │(Framework)│    │ (Parser) │    │ (Logic)  │             │
│   └──────────┘    └──────────┘    └────┬─────┘    └────┬─────┘             │
│         │              │               │               │                    │
│         │              │         ┌─────┴─────┐         │                    │
│   Section          Resolve Path  │   Tools    │    Section                   │
│   1+2+3+4         ${VAR}     │(Constrained)│    2+3+4.2                   │
│                               └───────────┘    + Agent A                   │
│                                                + YAML Template              │
│                                                                              │
│   Information Isolation:                                                     │
│   - Agent A: Section 1 + 4.1 (Cannot see Check/Waiver Logic)                │
│   - Agent B: Section 2 + 3 + 4.2 (Cannot see Parsing Logic)                 │
│   - Both forbidden: Actual values of pattern_items/requirements.value       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Smart Repair Flow Diagram

```
                      ┌─────────────┐
                      │  Validator  │
                      └──────┬──────┘
                             │
                    ┌────────┴────────┐
                    │ determine_error │
                    │    _source()    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
     ┌───────────┐    ┌───────────┐    ┌───────────┐
     │ atom_a    │    │ atom_b/c  │    │  unknown  │
     │           │    │ or yaml   │    │           │
     └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
           │                │                │
           ▼                ▼                ▼
     ┌───────────┐    ┌───────────┐    ┌───────────┐
     │ reflect_a │    │ reflect_b │    │ reflect_a │
     │   Node    │    │   Node    │    │ (default) │
     └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
           │                │                │
           ▼                ▼                ▼
     ┌───────────┐    ┌───────────┐    ┌───────────┐
     │  Agent A  │    │  Agent B  │    │  Agent A  │
     │ (Rerun)   │    │ (Rerun)   │    │ (Rerun)   │
     └───────────┘    └───────────┘    └───────────┘
```

### 7.3 Tool Call Constraint Summary

| Constraint Type | Value | Description |
|---------|---|------|
| Max lines per read | 200 | Prevent reading entire file at once |
| Total read per session | 100KB | Prevent context overload |
| Max files per discovery | 20 | Limit file list size |
| Must discover first | Yes | Cannot skip discovery and read directly |
| Path variables | Framework preprocessed | LLM only sees absolute paths |

### 7.4 Cache Cleanup Timing

```python
# Suggested cleanup timing
cache = FileSystemCache("./cache")

# 1. On Agent startup, clean up data older than 24 hours
cache.cleanup_old_hours(item_id, keep_hours=24)

# 2. Automatically keep 10 most recent checkpoints per hour (auto-executed)
# See _cleanup_hourly_checkpoints()

# 3. Optional: Manual cleanup after successful completion
# if state['current_stage'] == 'done':
#     cache.cleanup_old_hours(item_id, keep_hours=1)
```
