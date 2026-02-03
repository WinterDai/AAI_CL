"""
Developer Agent - LangGraph Workflow Implementation
Based on Agent_Development_Spec.md v1.1 Section 6

Builds the LangGraph state machine for the agent workflow.
"""
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: langgraph not installed. Run: pip install langgraph")

from state import AgentState, AgentConfig, create_initial_state, generate_item_id
from cache import FileSystemCache, resume_from_checkpoint
from nodes import (
    load_spec_node,
    discover_logs_node,
    agent_a_node,
    agent_b_node,
    validate_node,
    reflect_a_node,
    reflect_b_node,
    human_required_node,
    should_continue,
    extract_stage_outputs
)


def build_agent_graph(config: AgentConfig = None):
    """
    Build LangGraph workflow with smart fix routing
    
    Returns:
        Compiled StateGraph
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph not installed. Install with:\n"
            "pip install langgraph"
        )
    
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("load_spec", lambda s: load_spec_node(s, config))
    graph.add_node("discover_logs", lambda s: discover_logs_node(s, config))
    graph.add_node("agent_a", lambda s: agent_a_node(s, config))
    graph.add_node("agent_b", lambda s: agent_b_node(s, config))
    graph.add_node("validate", validate_node)
    graph.add_node("reflect_a", lambda s: reflect_a_node(s, config))
    graph.add_node("reflect_b", lambda s: reflect_b_node(s, config))
    graph.add_node("human_required", human_required_node)
    
    # Add edges: Normal flow
    graph.add_edge("load_spec", "discover_logs")
    graph.add_edge("discover_logs", "agent_a")
    graph.add_edge("agent_a", "agent_b")
    graph.add_edge("agent_b", "validate")
    
    # Conditional edges: Smart fix routing
    max_iterations = config.max_iterations if config else 3
    
    graph.add_conditional_edges(
        "validate",
        lambda s: should_continue(s, max_iterations),
        {
            "done": END,
            "reflect_a": "reflect_a",
            "reflect_b": "reflect_b",
            "human_required": "human_required"
        }
    )
    
    # Smart fix: Route based on error source
    graph.add_edge("reflect_a", "agent_a")   # Atom A error → re-run Agent A → Agent B → Validate
    graph.add_edge("reflect_b", "agent_b")   # Atom B/C/YAML error → only re-run Agent B → Validate
    graph.add_edge("human_required", END)
    
    # Set entry point
    graph.set_entry_point("load_spec")
    
    return graph.compile()


def run_agent(
    item_spec_path: str,
    search_root: str = None,
    resume: bool = False,
    config_path: str = None
) -> AgentState:
    """
    Main entry point for running the agent
    
    Args:
        item_spec_path: Path to ItemSpec file
        search_root: Log file search root directory
        resume: Whether to resume from checkpoint
        config_path: Path to config file (optional)
        
    Returns:
        Final AgentState
    """
    # Load configuration
    config = AgentConfig.load(config_path)
    
    # Override search_root if provided
    if search_root:
        config.search_root = search_root
    
    # Initialize cache
    cache = FileSystemCache(config.cache_dir, config.max_checkpoints_per_hour)
    item_id = generate_item_id(item_spec_path)
    
    # Resume from checkpoint or create initial state
    if resume:
        state = resume_from_checkpoint(item_id, cache)
        if state is None:
            state = create_initial_state(item_spec_path, search_root)
        elif state.get("current_stage") in ("done", "human_required"):
            print(f"[INFO] Cannot resume from stage: {state['current_stage']}")
            return state
    else:
        state = create_initial_state(item_spec_path, search_root)
    
    # Cleanup old checkpoints
    cache.cleanup_old_hours(item_id, keep_hours=24)
    
    # Build and run graph
    graph = build_agent_graph(config)
    
    print(f"\n{'='*60}")
    print(f"Starting Agent for: {item_spec_path}")
    print(f"{'='*60}\n")
    
    # Stream execution with real-time state updates
    final_state = None
    for event in graph.stream(state):
        node_name = list(event.keys())[0]
        node_state = event[node_name]
        final_state = node_state
        
        # Save checkpoint after each node
        checkpoint_id = cache.save_checkpoint(item_id, node_state)
        cache.save_stage_output(item_id, node_name, {
            "timestamp": datetime.now().isoformat(),
            "checkpoint_id": checkpoint_id,
            "outputs": extract_stage_outputs(node_name, node_state)
        })
        
        # Print progress
        stage = node_state.get('current_stage', 'unknown')
        iteration = node_state.get('iteration_count', 0)
        errors = len(node_state.get('validation_errors', []))
        
        status_icon = "✓" if stage == "done" else "⚠️" if stage == "human_required" else "▶"
        print(f"{status_icon} [{stage}] Completed. Iteration: {iteration}, Errors: {errors}")
    
    # Final summary
    print(f"\n{'='*60}")
    if final_state.get("current_stage") == "done":
        print("✅ SUCCESS: Code generation completed!")
        print(f"   Output saved to: {config.output_dir}/{item_id}/")
    elif final_state.get("current_stage") == "human_required":
        print("⚠️  STOPPED: Human intervention required")
        print(f"   See report at: {config.cache_dir}/{item_id}/")
    print(f"{'='*60}\n")
    
    return final_state


def run_agent_simple(
    item_spec_path: str,
    config: AgentConfig = None,
    mock_llm: bool = False
) -> AgentState:
    """
    Simplified agent runner for testing
    
    Args:
        item_spec_path: Path to ItemSpec file
        config: Agent configuration (optional)
        mock_llm: Use mock LLM for testing
        
    Returns:
        Final AgentState
    """
    if config is None:
        try:
            config = AgentConfig.load()
        except FileNotFoundError:
            # Use default config for testing
            from state import LLMConfig
            config = AgentConfig(
                search_root="./test_logs",
                item_specs_dir="./item_specs",
                cache_dir="./cache",
                output_dir="./output",
                agent_a_llm=LLMConfig("jedai", "claude-3-7-sonnet", 0.2, 4096),
                agent_b_llm=LLMConfig("jedai", "claude-3-7-sonnet", 0.1, 4096),
                reflect_llm=LLMConfig("jedai", "claude-3-7-sonnet", 0.1, 2048),
                max_iterations=3,
                cache_retention_policy="hourly",
                max_checkpoints_per_hour=10,
                log_level="INFO",
                log_file="./logs/agent.log",
                log_llm_calls=True
            )
    
    # Create initial state
    state = create_initial_state(item_spec_path)
    
    # Run nodes sequentially (without LangGraph for simpler testing)
    from llm_client import MockLLMClient
    
    if mock_llm:
        llm_client = MockLLMClient()
    else:
        from llm_client import LLMClient
        llm_client = None  # Will use config defaults
    
    try:
        # Load spec
        state = load_spec_node(state, config)
        print(f"✓ load_spec: Loaded {state.get('parsed_spec', {}).get('item_id', 'unknown')}")
        
        # Discover logs
        state = discover_logs_node(state, config)
        print(f"✓ discover_logs: Found {len(state.get('discovered_log_files', []))} files")
        
        # Agent A
        if mock_llm:
            state = agent_a_node(state, config, MockLLMClient())
        else:
            state = agent_a_node(state, config)
        print(f"✓ agent_a: Generated {len(state.get('atom_a_code', ''))} chars")
        
        # Agent B
        if mock_llm:
            state = agent_b_node(state, config, MockLLMClient())
        else:
            state = agent_b_node(state, config)
        print(f"✓ agent_b: Generated B={len(state.get('atom_b_code', ''))}, C={len(state.get('atom_c_code', ''))}")
        
        # Validate
        state = validate_node(state)
        errors = state.get("validation_errors", [])
        print(f"✓ validate: {len(errors)} errors")
        
        if errors:
            print(f"  Errors: {errors[:3]}...")
        
        # Check if we need reflection
        iteration = 0
        while errors and iteration < config.max_iterations:
            iteration += 1
            error_source = state.get("error_source", "unknown")
            
            if error_source == "atom_a":
                if mock_llm:
                    state = reflect_a_node(state, config, MockLLMClient())
                    state = agent_a_node(state, config, MockLLMClient())
                else:
                    state = reflect_a_node(state, config)
                    state = agent_a_node(state, config)
            else:
                if mock_llm:
                    state = reflect_b_node(state, config, MockLLMClient())
                    state = agent_b_node(state, config, MockLLMClient())
                else:
                    state = reflect_b_node(state, config)
                    state = agent_b_node(state, config)
            
            state = validate_node(state)
            errors = state.get("validation_errors", [])
            print(f"✓ reflect_{error_source}/validate (iter {iteration}): {len(errors)} errors")
        
        if not errors:
            state["current_stage"] = "done"
            print("\n✅ SUCCESS: All validations passed!")
        else:
            state = human_required_node(state)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        state["validation_errors"] = [str(e)]
        state["current_stage"] = "error"
    
    return state


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Developer Agent CLI")
    parser.add_argument("--item", required=True, help="ItemSpec file path")
    parser.add_argument("--search-root", help="Log file search root")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM (for testing)")
    
    args = parser.parse_args()
    
    if args.mock:
        result = run_agent_simple(args.item, mock_llm=True)
    else:
        result = run_agent(
            item_spec_path=args.item,
            search_root=args.search_root,
            resume=args.resume,
            config_path=args.config
        )
    
    print(f"\nFinal stage: {result.get('current_stage')}")
    print(f"Iterations: {result.get('iteration_count', 0)}")
