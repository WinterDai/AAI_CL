"""Hints management module for user requirements tracking (JSON format)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def load_user_hints(item_id: str) -> Optional[Dict]:
    """
    Load historical hints from JSON file.
    
    Args:
        item_id: Checker item ID
        
    Returns:
        dict: {
            "item_id": str,
            "history": [{"timestamp": str, "hints": str, "author": str}, ...],
            "latest": {"timestamp": str, "hints": str, "author": str}
        }
        or None if file doesn't exist
    """
    hints_file = Path(f"Work/phase-1-dev/{item_id}/user_hints.json")
    
    if hints_file.exists():
        try:
            content = hints_file.read_text(encoding='utf-8')
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Failed to parse {hints_file}: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Warning: Failed to read {hints_file}: {e}")
            return None
    
    return None


def save_user_hints(item_id: str, hints: str, author: Optional[str] = None) -> None:
    """
    Save hints to JSON file (append mode with history tracking).
    
    Args:
        item_id: Checker item ID
        hints: User input hints content
        author: Author name (default: from USERNAME env var)
    """
    hints_file = Path(f"Work/phase-1-dev/{item_id}/user_hints.json")
    hints_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data
    if hints_file.exists():
        try:
            data = json.loads(hints_file.read_text(encoding='utf-8'))
        except:
            # If corrupted, start fresh
            data = {"item_id": item_id, "history": []}
    else:
        data = {"item_id": item_id, "history": []}
    
    # Create new entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "hints": hints,
        "author": author or os.getenv('USERNAME', 'unknown')
    }
    
    # Append to history
    data['history'].append(entry)
    data['latest'] = entry
    
    # Save (formatted, ensure Chinese is readable)
    hints_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    
    print(f"✓ Hints saved to {hints_file}")


def format_hints_for_display(hints_data: Dict) -> Optional[str]:
    """
    Format JSON data to human-readable string for display.
    
    Args:
        hints_data: Data returned by load_user_hints()
        
    Returns:
        Formatted multi-line string or None
    """
    if not hints_data or not hints_data.get('history'):
        return None
    
    lines = ["📜 Previous Hints History:", "=" * 60]
    
    for i, entry in enumerate(hints_data['history'], 1):
        timestamp = entry.get('timestamp', 'N/A')
        hints = entry.get('hints', '')
        author = entry.get('author', 'unknown')
        
        lines.append(f"\n[{i}] {timestamp} by {author}")
        # Indent multi-line hints
        indented_hints = hints.replace('\n', '\n    ')
        lines.append(f"    {indented_hints}")
    
    lines.append("=" * 60)
    return "\n".join(lines)


def load_batch_hints_config(config_file: str = "hints_config.json") -> Dict:
    """
    Load batch hints configuration from JSON file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        dict: {
            "IMP-15-0-0-01": {"hints": str, "priority": str, "tags": [...]},
            ...
        }
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    
    return json.loads(config_path.read_text(encoding='utf-8'))
