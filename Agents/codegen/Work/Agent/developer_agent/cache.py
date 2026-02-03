"""
Developer Agent - Cache Implementation
Based on Agent_Development_Spec.md v1.1

Implements FileSystemCache with hourly checkpoint organization and cleanup.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
import os
import shutil
from datetime import datetime, timedelta


class StateCache(ABC):
    """Abstract base class for state caching"""
    
    @abstractmethod
    def save_checkpoint(self, item_id: str, state: Dict[str, Any]) -> str:
        """Save checkpoint, return checkpoint_id"""
        pass
    
    @abstractmethod
    def load_checkpoint(self, item_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load checkpoint, default loads latest"""
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
    """
    File system based cache implementation with hourly organization
    
    Directory Structure:
        cache/
        ├── {item_id}/
        │   ├── checkpoint_latest.json
        │   ├── hourly/
        │   │   ├── 2026012814/
        │   │   │   ├── checkpoint_143025.json
        │   │   │   └── ...
        │   │   └── ...
        │   ├── stage_outputs/
        │   │   ├── load_spec.json
        │   │   └── ...
        │   └── error_logs/
        │       └── iteration_{n}.json
    """
    
    def __init__(self, cache_dir: str = "./cache", max_checkpoints_per_hour: int = 10):
        """
        Initialize FileSystemCache
        
        Args:
            cache_dir: Base directory for cache storage
            max_checkpoints_per_hour: Maximum checkpoints to retain per hour
        """
        self.cache_dir = cache_dir
        self.max_checkpoints_per_hour = max_checkpoints_per_hour
        os.makedirs(cache_dir, exist_ok=True)
    
    def save_checkpoint(self, item_id: str, state: Dict[str, Any]) -> str:
        """
        Save checkpoint with hourly organization
        
        Args:
            item_id: Item identifier
            state: State dictionary to save
            
        Returns:
            checkpoint_id in format "{hour_folder}_{time}"
        """
        now = datetime.now()
        hour_folder = now.strftime("%Y%m%d%H")  # e.g., "2026012814"
        checkpoint_id = now.strftime("%H%M%S")   # e.g., "143025"
        
        item_dir = os.path.join(self.cache_dir, item_id)
        hourly_dir = os.path.join(item_dir, "hourly", hour_folder)
        os.makedirs(hourly_dir, exist_ok=True)
        
        # Save to hourly directory
        checkpoint_path = os.path.join(hourly_dir, f"checkpoint_{checkpoint_id}.json")
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(dict(state), f, indent=2, ensure_ascii=False)
        
        # Update latest checkpoint
        latest_path = os.path.join(item_dir, "checkpoint_latest.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(dict(state), f, indent=2, ensure_ascii=False)
        
        # Cleanup old checkpoints in current hour
        self._cleanup_hourly_checkpoints(hourly_dir)
        
        return f"{hour_folder}_{checkpoint_id}"
    
    def _cleanup_hourly_checkpoints(self, hourly_dir: str) -> None:
        """
        Retain only the most recent N checkpoints per hour
        
        Args:
            hourly_dir: Directory to clean up
        """
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
        Remove hourly checkpoint directories older than specified hours
        
        Args:
            item_id: Item identifier
            keep_hours: Number of hours to retain
        """
        hourly_base = os.path.join(self.cache_dir, item_id, "hourly")
        if not os.path.exists(hourly_base):
            return
        
        cutoff = datetime.now() - timedelta(hours=keep_hours)
        cutoff_folder = cutoff.strftime("%Y%m%d%H")
        
        for folder in os.listdir(hourly_base):
            if folder < cutoff_folder:
                folder_path = os.path.join(hourly_base, folder)
                shutil.rmtree(folder_path)
                print(f"[Cache] Removed old hourly folder: {folder}")
    
    def load_checkpoint(self, item_id: str, checkpoint_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint
        
        Args:
            item_id: Item identifier
            checkpoint_id: Checkpoint ID in format "{hour_folder}_{time}" (e.g., "2026012814_143025")
                          If None, loads the latest checkpoint
                          
        Returns:
            State dictionary or None if not found
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
        """
        Save output for a specific stage
        
        Args:
            item_id: Item identifier
            stage: Stage name (e.g., "load_spec", "agent_a")
            output: Output dictionary to save
        """
        stage_dir = os.path.join(self.cache_dir, item_id, "stage_outputs")
        os.makedirs(stage_dir, exist_ok=True)
        
        path = os.path.join(stage_dir, f"{stage}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def load_stage_output(self, item_id: str, stage: str) -> Optional[dict]:
        """
        Load output for a specific stage
        
        Args:
            item_id: Item identifier
            stage: Stage name
            
        Returns:
            Output dictionary or None if not found
        """
        path = os.path.join(self.cache_dir, item_id, "stage_outputs", f"{stage}.json")
        
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_error_log(self, item_id: str, iteration: int, error_data: dict) -> None:
        """
        Save error log for a specific iteration
        
        Args:
            item_id: Item identifier
            iteration: Iteration number
            error_data: Error details dictionary
        """
        error_dir = os.path.join(self.cache_dir, item_id, "error_logs")
        os.makedirs(error_dir, exist_ok=True)
        
        path = os.path.join(error_dir, f"iteration_{iteration}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
    
    def list_checkpoints(self, item_id: str) -> list:
        """
        List all available checkpoints for an item
        
        Args:
            item_id: Item identifier
            
        Returns:
            List of checkpoint_ids sorted by time
        """
        checkpoints = []
        hourly_base = os.path.join(self.cache_dir, item_id, "hourly")
        
        if not os.path.exists(hourly_base):
            return checkpoints
        
        for hour_folder in sorted(os.listdir(hourly_base)):
            hour_path = os.path.join(hourly_base, hour_folder)
            if os.path.isdir(hour_path):
                for f in sorted(os.listdir(hour_path)):
                    if f.startswith("checkpoint_") and f.endswith(".json"):
                        time_part = f.replace("checkpoint_", "").replace(".json", "")
                        checkpoints.append(f"{hour_folder}_{time_part}")
        
        return checkpoints
    
    def get_cache_stats(self, item_id: str) -> dict:
        """
        Get statistics about cache for an item
        
        Args:
            item_id: Item identifier
            
        Returns:
            Statistics dictionary
        """
        item_dir = os.path.join(self.cache_dir, item_id)
        
        if not os.path.exists(item_dir):
            return {"exists": False}
        
        stats = {
            "exists": True,
            "total_checkpoints": len(self.list_checkpoints(item_id)),
            "has_latest": os.path.exists(os.path.join(item_dir, "checkpoint_latest.json")),
            "stages": []
        }
        
        stage_dir = os.path.join(item_dir, "stage_outputs")
        if os.path.exists(stage_dir):
            stats["stages"] = [f.replace(".json", "") for f in os.listdir(stage_dir) if f.endswith(".json")]
        
        return stats


def resume_from_checkpoint(item_id: str, cache: StateCache) -> Optional[Dict[str, Any]]:
    """
    Resume execution from the latest checkpoint
    
    Args:
        item_id: Item identifier
        cache: Cache instance
        
    Returns:
        Loaded state or None
    """
    state = cache.load_checkpoint(item_id)
    
    if state is None:
        print(f"[INFO] No checkpoint found for {item_id}, starting fresh")
        return None
    
    stage = state.get('current_stage', 'init')
    
    if stage == "done":
        print(f"[INFO] Item {item_id} already completed")
        return state
    
    if stage == "human_required":
        print(f"[WARN] Item {item_id} requires human intervention, cannot auto-resume")
        return state
    
    print(f"[INFO] Resuming from stage '{stage}'")
    return state


# =============================================================================
# Context Maintenance Utilities
# =============================================================================

def update_conversation_summary(state: Dict[str, Any], new_summary: str) -> Dict[str, Any]:
    """
    Update the conversation summary in state (avoid forgetting key context)
    
    Args:
        state: Current agent state
        new_summary: New summary to append/replace
        
    Returns:
        Updated state
    """
    state["conversation_summary"] = new_summary
    state["updated_at"] = datetime.now().isoformat()
    return state


def record_key_decision(state: Dict[str, Any], decision: str, reason: str) -> Dict[str, Any]:
    """
    Record a key decision made during iteration
    
    Args:
        state: Current agent state
        decision: The decision made
        reason: Reasoning behind the decision
        
    Returns:
        Updated state
    """
    if "key_decisions" not in state:
        state["key_decisions"] = []
    
    iteration = state.get("iteration_count", 0)
    state["key_decisions"].append({
        "round": str(iteration + 1),
        "decision": decision,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    })
    state["updated_at"] = datetime.now().isoformat()
    return state


def update_iteration_context(state: Dict[str, Any], context_key: str, context_value: Any) -> Dict[str, Any]:
    """
    Update iteration context for passing information between iterations
    
    Args:
        state: Current agent state
        context_key: Key for the context item
        context_value: Value to store
        
    Returns:
        Updated state
    """
    if "iteration_context" not in state:
        state["iteration_context"] = {}
    
    state["iteration_context"][context_key] = context_value
    state["updated_at"] = datetime.now().isoformat()
    return state


def get_context_summary(state: Dict[str, Any]) -> str:
    """
    Generate a summary of current context for debugging/logging
    
    Args:
        state: Current agent state
        
    Returns:
        Human-readable context summary
    """
    lines = []
    lines.append(f"=== Context Summary ===")
    lines.append(f"Stage: {state.get('current_stage', 'unknown')}")
    lines.append(f"Iteration: {state.get('iteration_count', 0)}")
    
    if state.get("generated_code_signatures"):
        lines.append(f"Generated Functions: {list(state['generated_code_signatures'].keys())}")
    
    if state.get("key_decisions"):
        lines.append(f"Key Decisions: {len(state['key_decisions'])}")
        for d in state["key_decisions"][-3:]:  # Show last 3
            lines.append(f"  - Round {d['round']}: {d['decision']}")
    
    if state.get("conversation_summary"):
        lines.append(f"Summary: {state['conversation_summary'][:200]}...")
    
    return "\n".join(lines)
