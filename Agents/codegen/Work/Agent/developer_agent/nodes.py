"""
Developer Agent - Graph Nodes Implementation
Based on Agent_Development_Spec.md v1.1 Section 5.3

Implements all LangGraph node functions with cache integration.
Explicitly prints prompts and responses for debugging per user requirement.
Uses io_formatter for readable Markdown-style output.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import os

from state import AgentState, AgentConfig, generate_item_id
from cache import FileSystemCache
from tools import (
    parse_item_spec,
    discover_files,
    extract_snippet,
    extract_file_patterns_from_spec,
    extract_keywords_from_spec
)
from validator import validate_10_2_compliance, determine_error_source
from llm_client import LLMClient, get_llm_client
from prompts import (
    build_agent_a_prompt,
    build_agent_b_prompt,
    build_reflect_prompt,
    parse_agent_response,
    parse_agent_b_response
)
from io_formatter import (
    print_formatted_prompt,
    print_formatted_response,
    print_formatted_validation,
    save_io_as_markdown
)


# Global cache instance
_cache: Optional[FileSystemCache] = None

# Verbosity control for prompt/response printing
_verbose_mode: bool = True

# Markdown output directory (set by caller)
_markdown_output_dir: Optional[str] = None


def set_verbose_mode(enabled: bool):
    """Enable or disable verbose prompt/response printing"""
    global _verbose_mode
    _verbose_mode = enabled


def set_markdown_output_dir(output_dir: str):
    """Set the directory for saving Markdown formatted I/O files"""
    global _markdown_output_dir
    _markdown_output_dir = output_dir


def _print_prompt_response(stage: str, prompt: str, response: str, item_id: str = None, iteration: int = 0):
    """
    Print prompt and response with Markdown formatting for debugging
    
    Args:
        stage: Stage name (e.g., "agent_a", "agent_b", "reflect_a")
        prompt: The prompt sent to LLM
        response: The response received from LLM
        item_id: Optional item ID for saving markdown files
        iteration: Current iteration round (0-based)
    """
    if not _verbose_mode:
        return
    
    # Print formatted to console
    print_formatted_prompt(stage, prompt)
    print_formatted_response(stage, response)
    
    # Save as Markdown files if output dir is set
    if _markdown_output_dir and item_id:
        save_io_as_markdown(
            output_dir=_markdown_output_dir,
            item_id=item_id,
            stage=stage,
            prompt=prompt,
            response=response,
            iteration=iteration
        )


def get_cache(cache_dir: str = "./cache") -> FileSystemCache:
    """Get or create the global cache instance"""
    global _cache
    if _cache is None:
        _cache = FileSystemCache(cache_dir)
    return _cache


def _save_stage_io(item_id: str, stage: str, inputs: Dict, outputs: Dict, cache: FileSystemCache = None):
    """
    Save stage input/output to cache for debugging and resume capability
    
    Args:
        item_id: Item identifier
        stage: Stage name (e.g., "load_spec", "agent_a")
        inputs: Input dictionary for this stage
        outputs: Output dictionary from this stage
        cache: Optional cache instance
    """
    if cache is None:
        cache = get_cache()
    
    stage_data = {
        "timestamp": datetime.now().isoformat(),
        "stage": stage,
        "inputs": inputs,
        "outputs": outputs
    }
    
    cache.save_stage_output(item_id, stage, stage_data)
    print(f"[Cache] Saved stage '{stage}' I/O for item '{item_id}'")


def load_spec_node(state: AgentState, config: AgentConfig = None) -> AgentState:
    """
    Load and parse ItemSpec file
    
    Input:
        - state["item_spec_path"]: ItemSpec file path
    
    Output:
        - state["item_spec_content"]: Raw content
        - state["parsed_spec"]: Structured parse result
    """
    state["current_stage"] = "load_spec"
    
    if config is None:
        config = AgentConfig.load()
    
    # Record inputs for caching
    stage_inputs = {
        "item_spec_path": state.get("item_spec_path", "")
    }
    
    # Load ItemSpec file
    spec_path = os.path.join(config.item_specs_dir, state["item_spec_path"])
    
    if not os.path.exists(spec_path):
        # Try absolute path
        if os.path.exists(state["item_spec_path"]):
            spec_path = state["item_spec_path"]
        else:
            raise FileNotFoundError(f"ItemSpec not found: {spec_path}")
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        state["item_spec_content"] = f.read()
    
    # Parse ItemSpec
    state["parsed_spec"] = parse_item_spec(state["item_spec_content"])
    
    # Generate item_id from spec path if not already set
    if not state.get("item_id"):
        state["item_id"] = generate_item_id(state["item_spec_path"])
    
    state["updated_at"] = datetime.now().isoformat()
    
    # Cache stage I/O
    stage_outputs = {
        "item_spec_content": state["item_spec_content"],
        "parsed_spec": state["parsed_spec"],
        "item_id": state["item_id"]
    }
    _save_stage_io(state["item_id"], "load_spec", stage_inputs, stage_outputs)
    
    return state


def discover_logs_node(state: AgentState, config: AgentConfig = None) -> AgentState:
    """
    Discover relevant log files and extract samples
    
    Uses tools:
        - discover_files: Find matching log files
        - extract_snippet: Extract key snippets
    
    Output:
        - state["discovered_log_files"]: List of discovered files
        - state["log_snippets"]: Extracted log snippets
    """
    state["current_stage"] = "discover"
    
    if config is None:
        config = AgentConfig.load()
    
    # Record inputs for caching
    stage_inputs = {
        "parsed_spec": state.get("parsed_spec", {}),
        "search_root": config.search_root
    }
    
    # Extract file patterns from ItemSpec
    file_patterns = extract_file_patterns_from_spec(state.get("parsed_spec", {}))
    
    # Discover files
    all_files = []
    search_root = config.search_root
    
    if os.path.exists(search_root):
        for pattern in file_patterns:
            result = discover_files(
                base_path=search_root,
                pattern=pattern,
                limit=5
            )
            all_files.extend(result.get("matched_files", []))
    
    # Deduplicate and limit
    state["discovered_log_files"] = list(set(all_files))[:10]
    
    # Extract key snippets
    keywords = extract_keywords_from_spec(state.get("parsed_spec", {}))
    snippets = {}
    
    for file_path in state["discovered_log_files"]:
        try:
            snippet_result = extract_snippet(file_path, keywords)
            snippets[file_path] = snippet_result
        except Exception as e:
            snippets[file_path] = {"error": str(e)}
    
    state["log_snippets"] = snippets
    state["updated_at"] = datetime.now().isoformat()
    
    # Cache stage I/O
    item_id = state.get("item_id", "unknown")
    stage_outputs = {
        "discovered_log_files": state["discovered_log_files"],
        "log_snippets": snippets
    }
    _save_stage_io(item_id, "discover_logs", stage_inputs, stage_outputs)
    
    return state


def agent_a_node(state: AgentState, config: AgentConfig = None, llm_client: LLMClient = None) -> AgentState:
    """
    Agent A: Generate Atom A (extract_context)
    
    Uses Agent A Prompt template with:
        - ItemSpec Section 1 (Parsing Logic) + Section 4.1 (Implementation Guide)
        - Log sample snippets
    
    Output:
        - state["atom_a_code"]: extract_context function code
        - state["atom_a_reasoning"]: Reasoning process
        - state["generated_code_signatures"]: Updated function signatures cache
    """
    state["current_stage"] = "agent_a"
    
    if config is None:
        config = AgentConfig.load()
    
    if llm_client is None:
        llm_client = LLMClient(config.agent_a_llm)
    
    # Record inputs for caching
    item_id = state.get("item_id", "unknown")
    stage_inputs = {
        "item_spec_content_length": len(state.get("item_spec_content", "")),
        "log_snippets_count": len(state.get("log_snippets", {})),
        "model": config.agent_a_llm.model
    }
    
    # Build Agent A Prompt
    prompt = build_agent_a_prompt(
        item_spec_content=state.get("item_spec_content", ""),
        log_snippets=state.get("log_snippets", {}),
        parsed_spec=state.get("parsed_spec", {})
    )
    
    # Invoke LLM
    response = llm_client.invoke(prompt)
    
    # Print prompt and response for debugging (Markdown formatted)
    _print_prompt_response("agent_a", prompt, response, item_id)
    
    # Parse response
    atom_a_code, reasoning = parse_agent_response(response)
    
    state["atom_a_code"] = atom_a_code
    state["atom_a_reasoning"] = reasoning
    state["updated_at"] = datetime.now().isoformat()
    
    # Update context maintenance: cache generated code signature
    state["generated_code_signatures"] = state.get("generated_code_signatures", {})
    state["generated_code_signatures"]["extract_context"] = "def extract_context(text: str, source_file: str) -> List[Dict]"
    
    # Cache stage I/O (save full prompt and response for debugging)
    stage_outputs = {
        "prompt": prompt,
        "response": response,
        "atom_a_code": atom_a_code,
        "atom_a_reasoning": reasoning
    }
    _save_stage_io(item_id, "agent_a", stage_inputs, stage_outputs)
    
    return state


def agent_b_node(state: AgentState, config: AgentConfig = None, llm_client: LLMClient = None) -> AgentState:
    """
    Agent B: Generate Atom B, C and YAML configuration
    
    Section Delivery Strategy:
        In LangGraph mode, ALL sections (2 + 3 + 4.2) are provided in a SINGLE prompt.
        This ensures complete context for understanding validation items and waiver relationships.
    
    Uses Agent B Prompt template with:
        - ItemSpec Section 2 (Check Logic) + Section 3 (Waiver Logic) + Section 4.2 (Special Scenarios)
        - Agent A's extract_context code
        - YAML Template with field semantics reference
    
    Output:
        - state["atom_b_code"]: validate_logic function code
        - state["atom_c_code"]: check_existence function code
        - state["yaml_config"]: YAML configuration
        - state["atom_b_reasoning"]: Reasoning process
        - state["generated_code_signatures"]: Updated function signatures cache
    """
    state["current_stage"] = "agent_b"
    
    if config is None:
        config = AgentConfig.load()
    
    if llm_client is None:
        llm_client = LLMClient(config.agent_b_llm)
    
    # Record inputs for caching
    item_id = state.get("item_id", "unknown")
    stage_inputs = {
        "item_spec_content_length": len(state.get("item_spec_content", "")),
        "atom_a_code_length": len(state.get("atom_a_code", "")),
        "model": config.agent_b_llm.model
    }
    
    # Build Agent B Prompt (ALL sections delivered in single prompt)
    prompt = build_agent_b_prompt(
        item_spec_content=state.get("item_spec_content", ""),
        atom_a_code=state.get("atom_a_code", ""),
        parsed_spec=state.get("parsed_spec", {})
    )
    
    # Invoke LLM
    response = llm_client.invoke(prompt)
    
    # Print prompt and response for debugging (Markdown formatted)
    _print_prompt_response("agent_b", prompt, response, item_id)
    
    # Parse response
    atom_b_code, atom_c_code, yaml_config, reasoning = parse_agent_b_response(response)
    
    state["atom_b_code"] = atom_b_code
    state["atom_c_code"] = atom_c_code
    state["yaml_config"] = yaml_config
    state["atom_b_reasoning"] = reasoning
    state["updated_at"] = datetime.now().isoformat()
    
    # Update context maintenance: cache generated code signatures
    state["generated_code_signatures"] = state.get("generated_code_signatures", {})
    if atom_b_code:
        state["generated_code_signatures"]["validate_logic"] = "def validate_logic(text, pattern, parsed_fields=None, default_match='contains', regex_mode='search')"
    if atom_c_code:
        state["generated_code_signatures"]["check_existence"] = "def check_existence(items: List[Dict]) -> Dict"
    
    # Cache stage I/O (save full prompt and response for debugging)
    stage_outputs = {
        "prompt": prompt,
        "response": response,
        "atom_b_code": atom_b_code,
        "atom_c_code": atom_c_code,
        "yaml_config": yaml_config,
        "atom_b_reasoning": reasoning
    }
    _save_stage_io(item_id, "agent_b", stage_inputs, stage_outputs)
    
    return state


def validate_node(state: AgentState) -> AgentState:
    """
    Validation node: Invoke three-layer validator
    
    Validates:
        - Gate 1: AST static check
        - Gate 2: Runtime sandbox tests
        - Gate 3: Dual artifact consistency
    
    Output:
        - state["validation_errors"]: Error list
        - state["gate_results"]: Gate test results
        - state["error_source"]: Error source determination
    """
    state["current_stage"] = "validate"
    
    item_id = state.get("item_id", "unknown")
    
    # Combine all code
    full_code = f'''
{state.get("atom_a_code", "")}

{state.get("atom_b_code", "")}

{state.get("atom_c_code", "")}
'''
    
    # Invoke validator
    validation_result = validate_10_2_compliance(
        full_code, 
        state.get("yaml_config", "")
    )
    
    state["validation_errors"] = validation_result.get("errors", [])
    state["gate_results"] = validation_result.get("gate_results", {})
    
    # Determine error source if errors exist
    if state["validation_errors"]:
        state["error_source"] = determine_error_source(state["validation_errors"])
    else:
        state["error_source"] = ""
    
    state["updated_at"] = datetime.now().isoformat()
    
    # Cache validation results
    stage_outputs = {
        "validation_errors": state["validation_errors"],
        "gate_results": state["gate_results"],
        "error_source": state["error_source"],
        "full_code_length": len(full_code)
    }
    _save_stage_io(item_id, "validate", {"code_combined": True}, stage_outputs)
    
    return state


def reflect_a_node(state: AgentState, config: AgentConfig = None, llm_client: LLMClient = None) -> AgentState:
    """
    Reflect Node for Atom A:
    Only fix extract_context, preserve Agent B cached results
    """
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["current_stage"] = "reflect_a"
    
    # Record error history
    error_entry = {
        "iteration": state["iteration_count"],
        "errors": state.get("validation_errors", []),
        "source": "atom_a",
        "timestamp": datetime.now().isoformat()
    }
    if "error_history" not in state:
        state["error_history"] = []
    state["error_history"].append(error_entry)
    
    if config is None:
        config = AgentConfig.load()
    
    if llm_client is None:
        llm_client = LLMClient(config.reflect_llm)
    
    # Build Reflect Prompt for Atom A
    prompt = build_reflect_prompt(
        validation_errors=state.get("validation_errors", []),
        gate_results=state.get("gate_results", {}),
        previous_code=state.get("atom_a_code", ""),
        error_source="atom_a"
    )
    
    # Invoke LLM
    response = llm_client.invoke(prompt)
    
    # Print prompt and response for debugging (Markdown formatted)
    item_id = state.get("item_id", "unknown")
    _print_prompt_response("reflect_a", prompt, response, item_id)
    
    # Parse response - update Atom A code
    atom_a_code, reasoning = parse_agent_response(response)
    state["atom_a_code"] = atom_a_code
    state["atom_a_reasoning"] = reasoning
    
    state["updated_at"] = datetime.now().isoformat()
    return state


def reflect_b_node(state: AgentState, config: AgentConfig = None, llm_client: LLMClient = None) -> AgentState:
    """
    Reflect Node for Atom B/C/YAML:
    Only fix validate_logic/check_existence/YAML, reuse Agent A results
    """
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["current_stage"] = "reflect_b"
    
    # Record error history
    error_source = state.get("error_source", "atom_b")
    error_entry = {
        "iteration": state["iteration_count"],
        "errors": state.get("validation_errors", []),
        "source": error_source,
        "timestamp": datetime.now().isoformat()
    }
    if "error_history" not in state:
        state["error_history"] = []
    state["error_history"].append(error_entry)
    
    if config is None:
        config = AgentConfig.load()
    
    if llm_client is None:
        llm_client = LLMClient(config.reflect_llm)
    
    # Build Reflect Prompt for Atom B/C
    previous_code = f'''
# Atom B
{state.get("atom_b_code", "")}

# Atom C
{state.get("atom_c_code", "")}
'''
    
    prompt = build_reflect_prompt(
        validation_errors=state.get("validation_errors", []),
        gate_results=state.get("gate_results", {}),
        previous_code=previous_code,
        error_source=error_source
    )
    
    # Invoke LLM
    response = llm_client.invoke(prompt)
    
    # Print prompt and response for debugging (Markdown formatted)
    item_id = state.get("item_id", "unknown")
    _print_prompt_response("reflect_b", prompt, response, item_id)
    
    # Parse response - update Atom B/C code
    atom_b_code, atom_c_code, yaml_config, reasoning = parse_agent_b_response(response)
    if atom_b_code:
        state["atom_b_code"] = atom_b_code
    if atom_c_code:
        state["atom_c_code"] = atom_c_code
    if yaml_config:
        state["yaml_config"] = yaml_config
    state["atom_b_reasoning"] = reasoning
    
    state["updated_at"] = datetime.now().isoformat()
    return state


def human_required_node(state: AgentState, cache: FileSystemCache = None) -> AgentState:
    """
    Human intervention node: Generate report and stop execution
    """
    state["current_stage"] = "human_required"
    
    # Generate human intervention report
    report = generate_human_intervention_report(state)
    
    # Save report
    if cache is None:
        cache = FileSystemCache()
    
    item_id = generate_item_id(state.get("item_spec_path", "unknown"))
    cache.save_stage_output(item_id, "human_intervention_report", report)
    
    # Print report summary
    print("\n" + "=" * 60)
    print("⚠️  HUMAN INTERVENTION REQUIRED")
    print("=" * 60)
    print(f"Item: {report['item_id']}")
    print(f"Iterations: {report['total_iterations']}")
    print(f"Last Errors: {report['last_validation_errors'][:3] if len(report['last_validation_errors']) > 3 else report['last_validation_errors']}")
    print(f"Report saved to: {report['cache_location']}")
    print(f"Resume with: {report['resume_command']}")
    print("=" * 60 + "\n")
    
    state["updated_at"] = datetime.now().isoformat()
    return state


def generate_human_intervention_report(state: AgentState) -> Dict[str, Any]:
    """
    Generate human intervention report when iteration_count >= 3
    
    Returns:
        Report dictionary with failure details and suggested actions
    """
    item_id = generate_item_id(state.get("item_spec_path", "unknown"))
    
    report = {
        "status": "HUMAN_INTERVENTION_REQUIRED",
        "item_id": item_id,
        "total_iterations": state.get("iteration_count", 0),
        "failure_summary": f"Failed to generate compliant code after {state.get('iteration_count', 0)} attempts",
        "error_history": state.get("error_history", []),
        "last_validation_errors": state.get("validation_errors", []),
        "last_gate_results": state.get("gate_results", {}),
        "last_error_source": state.get("error_source", "unknown"),
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
        "cache_location": f"./cache/{item_id}/",
        "resume_command": f"python main.py --resume --item {state.get('item_spec_path', '')}"
    }
    
    return report


def should_continue(state: AgentState, max_iterations: int = 3) -> str:
    """
    Conditional edge logic: Determine next node
    
    Smart fix strategy:
    - If error source is Atom A → only re-run Agent A, preserve Agent B cache
    - If error source is Atom B/C/YAML → only re-run Agent B, reuse Agent A result
    
    Returns:
        "done" | "reflect_a" | "reflect_b" | "human_required"
    """
    if not state.get("validation_errors"):
        return "done"
    
    if state.get("iteration_count", 0) >= max_iterations:
        return "human_required"
    
    # Smart routing based on error source
    error_source = state.get("error_source", "unknown")
    
    if error_source == "atom_a":
        return "reflect_a"
    else:
        return "reflect_b"


def extract_stage_outputs(node_name: str, state: AgentState) -> Dict[str, Any]:
    """
    Extract relevant outputs for a given stage
    
    Args:
        node_name: Name of the completed node
        state: Current state
        
    Returns:
        Dictionary of stage-specific outputs
    """
    outputs = {
        "stage": node_name,
        "timestamp": state.get("updated_at", datetime.now().isoformat())
    }
    
    if node_name == "load_spec":
        outputs["item_id"] = state.get("parsed_spec", {}).get("item_id", "")
        outputs["sections_found"] = list(state.get("parsed_spec", {}).keys())
    
    elif node_name == "discover_logs":
        outputs["files_found"] = len(state.get("discovered_log_files", []))
        outputs["snippets_extracted"] = len(state.get("log_snippets", {}))
    
    elif node_name == "agent_a":
        outputs["code_length"] = len(state.get("atom_a_code", ""))
        outputs["has_standardization"] = "Standardization Layer" in state.get("atom_a_code", "")
    
    elif node_name == "agent_b":
        outputs["atom_b_length"] = len(state.get("atom_b_code", ""))
        outputs["atom_c_length"] = len(state.get("atom_c_code", ""))
        outputs["yaml_length"] = len(state.get("yaml_config", ""))
    
    elif node_name == "validate":
        outputs["valid"] = len(state.get("validation_errors", [])) == 0
        outputs["error_count"] = len(state.get("validation_errors", []))
        outputs["gate_results"] = state.get("gate_results", {})
    
    elif node_name in ("reflect_a", "reflect_b"):
        outputs["iteration"] = state.get("iteration_count", 0)
        outputs["error_source"] = state.get("error_source", "")
    
    return outputs
