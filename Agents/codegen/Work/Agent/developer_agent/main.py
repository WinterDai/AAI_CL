"""
Developer Agent - Main Entry Point
Based on Agent_Development_Spec.md v1.1

Provides CLI interface and programmatic API for running the agent.
"""
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Ensure module can be run from any directory
sys.path.insert(0, str(Path(__file__).parent))

from state import AgentConfig, create_initial_state, generate_item_id
from cache import FileSystemCache
from graph import run_agent, run_agent_simple


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Developer Agent - Generate 10.2 compliant Atom code from ItemSpec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with ItemSpec file
  python main.py --item IMP-10-0-0-00_ItemSpec.md
  
  # Resume from checkpoint
  python main.py --item IMP-10-0-0-00_ItemSpec.md --resume
  
  # Use custom search root
  python main.py --item IMP-10-0-0-00_ItemSpec.md --search-root /project/logs
  
  # Test with mock LLM
  python main.py --item IMP-10-0-0-00_ItemSpec.md --mock
  
  # List cached checkpoints
  python main.py --list-cache IMP-10-0-0-00
"""
    )
    
    parser.add_argument(
        "--item", "-i",
        help="Path to ItemSpec file"
    )
    parser.add_argument(
        "--search-root", "-s",
        help="Root directory for log file search"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Resume from latest checkpoint"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to config file"
    )
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Use mock LLM for testing (no real API calls)"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simplified runner (without LangGraph)"
    )
    parser.add_argument(
        "--list-cache",
        metavar="ITEM_ID",
        help="List cached checkpoints for an item"
    )
    parser.add_argument(
        "--cache-stats",
        metavar="ITEM_ID",
        help="Show cache statistics for an item"
    )
    parser.add_argument(
        "--cleanup-cache",
        metavar="ITEM_ID",
        help="Cleanup old cache for an item (keeps last 24 hours)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Developer Agent v1.0 (Based on Agent_Development_Spec v1.1)"
    )
    
    args = parser.parse_args()
    
    # Handle cache operations
    if args.list_cache:
        list_cache_checkpoints(args.list_cache)
        return
    
    if args.cache_stats:
        show_cache_stats(args.cache_stats)
        return
    
    if args.cleanup_cache:
        cleanup_cache(args.cleanup_cache)
        return
    
    # Require --item for main operations
    if not args.item:
        parser.print_help()
        print("\nError: --item is required for running the agent")
        sys.exit(1)
    
    # Run the agent
    try:
        if args.mock or args.simple:
            print(f"\n{'='*60}")
            print("Running in SIMPLE/MOCK mode")
            print(f"{'='*60}\n")
            result = run_agent_simple(
                item_spec_path=args.item,
                mock_llm=args.mock
            )
        else:
            result = run_agent(
                item_spec_path=args.item,
                search_root=args.search_root,
                resume=args.resume,
                config_path=args.config
            )
        
        # Exit code based on result
        if result.get("current_stage") == "done":
            sys.exit(0)
        elif result.get("current_stage") == "human_required":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


def list_cache_checkpoints(item_id: str):
    """List all cached checkpoints for an item"""
    cache = FileSystemCache()
    checkpoints = cache.list_checkpoints(item_id)
    
    if not checkpoints:
        print(f"No checkpoints found for item: {item_id}")
        return
    
    print(f"\nCheckpoints for {item_id}:")
    print("-" * 40)
    for cp in checkpoints:
        print(f"  {cp}")
    print(f"\nTotal: {len(checkpoints)} checkpoints")


def show_cache_stats(item_id: str):
    """Show cache statistics for an item"""
    cache = FileSystemCache()
    stats = cache.get_cache_stats(item_id)
    
    if not stats.get("exists"):
        print(f"No cache found for item: {item_id}")
        return
    
    print(f"\nCache Statistics for {item_id}:")
    print("-" * 40)
    print(f"  Total checkpoints: {stats.get('total_checkpoints', 0)}")
    print(f"  Has latest: {stats.get('has_latest', False)}")
    print(f"  Stages: {', '.join(stats.get('stages', []))}")


def cleanup_cache(item_id: str, keep_hours: int = 24):
    """Cleanup old cache for an item"""
    cache = FileSystemCache()
    print(f"Cleaning up cache for {item_id} (keeping last {keep_hours} hours)...")
    cache.cleanup_old_hours(item_id, keep_hours)
    print("Done.")


# Programmatic API
def run_from_code(
    item_spec_path: str,
    search_root: str = None,
    config: AgentConfig = None,
    resume: bool = False,
    mock_llm: bool = False
):
    """
    Run the agent programmatically
    
    Args:
        item_spec_path: Path to ItemSpec file
        search_root: Log file search root (optional)
        config: AgentConfig instance (optional)
        resume: Resume from checkpoint
        mock_llm: Use mock LLM
        
    Returns:
        Final AgentState dictionary
    """
    if mock_llm:
        return run_agent_simple(item_spec_path, config, mock_llm=True)
    else:
        return run_agent(
            item_spec_path=item_spec_path,
            search_root=search_root,
            resume=resume
        )


if __name__ == "__main__":
    main()
