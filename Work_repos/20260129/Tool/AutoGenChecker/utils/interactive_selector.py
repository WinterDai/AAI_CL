"""Interactive selector for CLI parameters."""

from __future__ import annotations

import sys
import yaml
from pathlib import Path
from typing import Optional


def select_llm_provider() -> tuple[str, str]:
    """
    Interactive LLM provider and model selection.
    
    Returns:
        Tuple of (provider, model)
    """
    print("\n┌─ LLM Provider Selection ──────────────────────────────────────────────────┐")
    print("│                                                                            │")
    print("│  [1] JEDAI (Cadence Internal)                                             │")
    print("│      • Claude Sonnet 4.5  • Claude Sonnet 3.5                             │")
    print("│      • Recommended for Cadence users ⭐                                    │")
    print("│                                                                            │")
    print("│  [2] OpenAI                                                                │")
    print("│      • GPT-4  • GPT-3.5-turbo                                              │")
    print("│                                                                            │")
    print("│  [3] Anthropic                                                             │")
    print("│      • Claude 3 Opus  • Claude 3 Sonnet                                    │")
    print("│                                                                            │")
    print("└───────────────────────────────────────────────────────────────────────────┘")
    
    while True:
        choice = input("\nYour choice [1-3, default=1] ► ").strip() or "1"
        
        if choice == "1":
            print("\n┌─ [JEDAI] Model Family Selection ─────────────────────────────────────────┐")
            print("│  [1] Claude (Recommended) ⭐                                              │")
            print("│  [2] Gemini                                                               │")
            print("│  [3] Meta-Llama                                                           │")
            print("│  [4] DeepSeek                                                             │")
            print("│  [5] Qwen                                                                 │")
            print("│  [6] Azure OpenAI                                                         │")
            print("└───────────────────────────────────────────────────────────────────────────┘")
            
            family_choice = input("\nYour choice [1-6, default=1] ► ").strip() or "1"
            
            if family_choice == "1":
                # Claude models
                print("\n┌─ [Claude] Model Selection ────────────────────────────────────────────────┐")
                print("│  [1] Claude Sonnet 4.5 (Latest, Recommended) ⭐                           │")
                print("│  [2] Claude Opus 4.1                                                      │")
                print("│  [3] Claude Opus 4                                                        │")
                print("│  [4] Claude Sonnet 4                                                      │")
                print("│  [5] Claude Haiku 4.5 (Fast)                                              │")
                print("│  [6] Claude 3.7 Sonnet                                                    │")
                print("│  [7] Claude 3.5 Sonnet                                                    │")
                print("│  [8] Claude 3 Opus                                                        │")
                print("└───────────────────────────────────────────────────────────────────────────┘")
                model_choice = input("\nYour choice [1-8, default=1] ► ").strip() or "1"
                
                model_map = {
                    "1": "claude-sonnet-4-5",
                    "2": "claude-opus-4-1",
                    "3": "claude-opus-4",
                    "4": "claude-sonnet-4",
                    "5": "claude-haiku-4-5",
                    "6": "claude-3-7-sonnet",
                    "7": "claude-3-5-sonnet",
                    "8": "claude-3-opus",
                }
                return ("jedai", model_map.get(model_choice, "claude-sonnet-4-5"))
            
            elif family_choice == "2":
                # Gemini models
                print("\n┌─ [Gemini] Model Selection ────────────────────────────────────────────────┐")
                print("│  [1] Gemini 2.5 Pro (Recommended) ⭐                                      │")
                print("│  [2] Gemini 2.5 Flash                                                     │")
                print("│  [3] Gemini 2.5 Flash Lite                                                │")
                print("│  [4] Gemini 1.5 Pro                                                       │")
                print("└───────────────────────────────────────────────────────────────────────────┘")
                model_choice = input("\nYour choice [1-4, default=1] ► ").strip() or "1"
                
                model_map = {
                    "1": "gemini-2-5-pro",
                    "2": "gemini-2-5-flash",
                    "3": "gemini-2-5-flash-lite",
                    "4": "gemini-1-5-pro",
                }
                return ("jedai", model_map.get(model_choice, "gemini-2-5-pro"))
            
            elif family_choice == "3":
                # Meta-Llama models
                print("\n┌─ [Meta-Llama] Model Selection ────────────────────────────────────────────┐")
                print("│  [1] Llama 4 Scout 17B (Latest) ⭐                                        │")
                print("│  [2] Llama 4 Maverick 17B                                                 │")
                print("│  [3] Llama 3.3 70B Instruct                                               │")
                print("│  [4] Llama 3.1 405B Instruct                                              │")
                print("│  [5] Llama 3.1 70B Instruct                                               │")
                print("│  [6] Llama 3.1 8B Instruct                                                │")
                print("└───────────────────────────────────────────────────────────────────────────┘")
                model_choice = input("\nYour choice [1-6, default=1] ► ").strip() or "1"
                
                model_map = {
                    "1": "meta-llama-4-scout-17b",
                    "2": "meta-llama-4-maverick-17b",
                    "3": "meta-llama-3-3-70b-instruct",
                    "4": "meta-llama-3-1-405b-instruct",
                    "5": "meta-llama-3-1-70b-instruct",
                    "6": "meta-llama-3-1-8b-instruct",
                }
                return ("jedai", model_map.get(model_choice, "meta-llama-4-scout-17b"))
            
            elif family_choice == "4":
                # DeepSeek models
                print("\n┌─ [DeepSeek] Model Selection ─────────────────────────────────────────────────┐")
                print("│  [1] DeepSeek V3.1 (Latest, Recommended) ⭐                                │")
                print("│  [2] DeepSeek R1                                                          │")
                print("└───────────────────────────────────────────────────────────────────────────┘")
                model_choice = input("\nYour choice [1-2, default=1] ► ").strip() or "1"
                
                model_map = {
                    "1": "deepseek-v3-1",
                    "2": "deepseek-r1",
                }
                return ("jedai", model_map.get(model_choice, "deepseek-v3-1"))
            
            elif family_choice == "5":
                # Qwen models
                print("\n┌─ [Qwen] Model Selection ─────────────────────────────────────────────────────┐")
                print("│  [1] Qwen3 Coder 480B (Coding optimized) ⭐                               │")
                print("│  [2] Qwen3 235B Instruct                                                  │")
                print("└───────────────────────────────────────────────────────────────────────────┘")
                model_choice = input("\nYour choice [1-2, default=1] ► ").strip() or "1"
                
                model_map = {
                    "1": "qwen3-coder-480b",
                    "2": "qwen3-235b-instruct",
                }
                return ("jedai", model_map.get(model_choice, "qwen3-coder-480b"))
            
            elif family_choice == "6":
                # Azure OpenAI models
                print("\n┌─ [Azure OpenAI] Model Selection ─────────────────────────────────────────────┐")
                print("│  [1] Azure GPT-5.2 (Latest) ⭐                                            │")
                print("│  [2] Azure GPT-5                                                          │")
                print("│  [3] Azure GPT-5 Mini                                                     │")
                print("│  [4] Azure GPT-4o                                                         │")
                print("│  [5] Azure GPT-4 Turbo                                                    │")
                print("│  [6] Azure o4-mini                                                        │")
                print("└───────────────────────────────────────────────────────────────────────────┘")
                model_choice = input("\nYour choice [1-6, default=1] ► ").strip() or "1"
                
                model_map = {
                    "1": "azure-gpt-5-2",
                    "2": "azure-gpt-5",
                    "3": "azure-gpt-5-mini",
                    "4": "azure-gpt-4o",
                    "5": "azure-gpt-4-turbo",
                    "6": "azure-o4-mini",
                }
                return ("jedai", model_map.get(model_choice, "azure-gpt-5-2"))
            
            else:
                print("❌ Invalid choice, using default (Claude Sonnet 4.5)")
                return ("jedai", "claude-sonnet-4-5")
        
        elif choice == "2":
            print("\n┌─ [OpenAI] Model Selection ───────────────────────────────────────────────────┐")
            print("│  [1] GPT-4 Turbo (Latest, Recommended) ⭐                                  │")
            print("│  [2] GPT-4                                                                │")
            print("│  [3] GPT-4-32k                                                            │")
            print("│  [4] GPT-3.5 Turbo                                                        │")
            print("│  [5] GPT-3.5 Turbo 16k                                                    │")
            print("└───────────────────────────────────────────────────────────────────────────┘")
            model_choice = input("\nYour choice [1-5, default=1] ► ").strip() or "1"
            
            model_map = {
                "1": "gpt-4-turbo",
                "2": "gpt-4",
                "3": "gpt-4-32k",
                "4": "gpt-3.5-turbo",
                "5": "gpt-3.5-turbo-16k",
            }
            
            if model_choice in model_map:
                return ("openai", model_map[model_choice])
            else:
                print("❌ Invalid choice, using default (GPT-4 Turbo)")
                return ("openai", "gpt-4-turbo")
        
        elif choice == "3":
            print("\n┌─ [Anthropic] Model Selection ────────────────────────────────────────────────┐")
            print("│  [1] Claude 3 Opus (Most capable) ⭐                                       │")
            print("│  [2] Claude 3 Sonnet (Balanced)                                           │")
            print("│  [3] Claude 3 Haiku (Fast & efficient)                                    │")
            print("│  [4] Claude 2.1                                                           │")
            print("│  [5] Claude 2.0                                                           │")
            print("└───────────────────────────────────────────────────────────────────────────┘")
            model_choice = input("\nYour choice [1-5, default=1] ► ").strip() or "1"
            
            model_map = {
                "1": "claude-3-opus-20240229",
                "2": "claude-3-sonnet-20240229",
                "3": "claude-3-haiku-20240307",
                "4": "claude-2.1",
                "5": "claude-2.0",
            }
            
            if model_choice in model_map:
                return ("anthropic", model_map[model_choice])
            else:
                print("❌ Invalid choice, using default (Claude 3 Opus)")
                return ("anthropic", "claude-3-opus-20240229")
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3")


def select_module(checklist_root: Path, recent_modules: list[str] | None = None) -> str:
    """
    Interactive module selection.
    
    Args:
        checklist_root: Path to CHECKLIST/Check_modules directory
        recent_modules: List of recently used modules
    
    Returns:
        Selected module name
    """
    # Discover all modules (exclude common directory)
    check_modules_dir = checklist_root / "Check_modules"
    if not check_modules_dir.exists():
        print(f"❌ Check_modules directory not found: {check_modules_dir}")
        raise FileNotFoundError(f"Check_modules not found: {check_modules_dir}")
    
    modules = sorted([d.name for d in check_modules_dir.iterdir() 
                     if d.is_dir() and not d.name.startswith('.') and d.name != 'common'])
    
    if not modules:
        print("❌ No modules found!")
        raise ValueError("No modules found in Check_modules directory")
    
    # Show recent modules first
    if recent_modules:
        print("\n┌─ Recently Used Modules ───────────────────────────────────────────────────┐")
        for i, mod in enumerate(recent_modules[:3], 1):
            if mod in modules:
                print(f"│  [{i}] {mod:<70} │")
        print("└───────────────────────────────────────────────────────────────────────────┘")
    
    # Show all modules
    print("\n┌─ All Available Modules ───────────────────────────────────────────────────┐")
    start_idx = len(recent_modules) if recent_modules else 0
    for i, mod in enumerate(modules, start_idx + 1):
        marker = " ⭐" if recent_modules and mod in recent_modules else "   "
        print(f"│  [{i:>2}] {mod:<67}{marker} │")
    print("└───────────────────────────────────────────────────────────────────────────┘")
    print(f"\n💡 Tip: Enter number [1-{len(modules) + start_idx}] or type module name directly")
    
    while True:
        choice = input("\nYour choice ► ").strip()
        
        if not choice:
            print("❌ Please enter a choice")
            continue
        
        # Check if it's a number
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= start_idx:
                # Recent module selection
                return recent_modules[idx - 1]
            elif start_idx < idx <= len(modules) + start_idx:
                # All modules selection
                return modules[idx - start_idx - 1]
            else:
                print(f"❌ Invalid number. Please enter 1-{len(modules) + start_idx}")
                continue
        
        # Check if it's a module name (partial match)
        matches = [m for m in modules if choice.lower() in m.lower()]
        
        if len(matches) == 1:
            print(f"✓ Selected: {matches[0]}")
            return matches[0]
        elif len(matches) > 1:
            print(f"\n⚠️  Multiple matches found:")
            for i, m in enumerate(matches, 1):
                print(f"  [{i}] {m}")
            sub_choice = input("Select one [1-{0}]: ".format(len(matches))).strip()
            if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(matches):
                return matches[int(sub_choice) - 1]
        else:
            print(f"❌ Module not found: {choice}")


def select_item(checklist_root: Path, module: str) -> str:
    """
    Interactive item selection.
    
    Args:
        checklist_root: Path to CHECKLIST directory
        module: Module name
    
    Returns:
        Selected item ID
    """
    print("\n" + "="*80)
    print(f"📝 Select Item from {module}")
    print("="*80)
    
    # Find items directory
    items_dir = checklist_root / "Check_modules" / module / "inputs" / "items"
    
    if not items_dir.exists():
        print(f"❌ Items directory not found: {items_dir}")
        raise FileNotFoundError(f"Items directory not found")
    
    # Load all item YAML files
    item_files = sorted(items_dir.glob("*.yaml"))
    
    if not item_files:
        print("❌ No items found!")
        raise ValueError(f"No item YAML files found in {items_dir}")
    
    # Parse items and show with descriptions
    items_data = []
    for item_file in item_files:
        item_id = item_file.stem
        try:
            with open(item_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                desc = data.get('description', 'N/A')
                items_data.append((item_id, desc))
        except Exception as e:
            items_data.append((item_id, f"Error loading: {e}"))
    
    # Show items (first 20 by default)
    show_limit = 20
    print(f"\n┌─ Available Items (showing {min(show_limit, len(items_data))}/{len(items_data)}) ─────────────────────────────────────────┐")
    print(f"│ {'#':<3} {'Item ID':<22} {'Description':<47} │")
    print("├─────┬──────────────────────┬───────────────────────────────────────────────┤")
    for i, (item_id, desc) in enumerate(items_data[:show_limit], 1):
        # Truncate long descriptions
        desc_short = desc[:45] + ".." if len(desc) > 45 else desc
        print(f"│ {i:<3} │ {item_id:<20} │ {desc_short:<45} │")
    print("└─────┴──────────────────────┴───────────────────────────────────────────────┘")
    
    if len(items_data) > show_limit:
        print(f"\n💡 {len(items_data) - show_limit} more items available - Type 'all' to see complete list")
    
    print(f"💡 Enter number [1-{len(items_data)}] or item ID (e.g., IMP-10-0-0-00)")
    
    while True:
        choice = input("\nYour choice ► ").strip()
        
        if not choice:
            print("❌ Please enter a choice")
            continue
        
        # Special command: show all
        if choice.lower() == 'all':
            print(f"\n┌─ All Items ({len(items_data)} total) ────────────────────────────────────────────────────┐")
            print(f"│ {'#':<3} {'Item ID':<22} {'Description':<47} │")
            print("├─────┬──────────────────────┬───────────────────────────────────────────────┤")
            for i, (item_id, desc) in enumerate(items_data, 1):
                desc_short = desc[:45] + ".." if len(desc) > 45 else desc
                print(f"│ {i:<3} │ {item_id:<20} │ {desc_short:<45} │")
            print("└─────┴──────────────────────┴───────────────────────────────────────────────┘")
            continue
        
        # Check if it's a number
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(items_data):
                selected_item = items_data[idx - 1][0]
                print(f"✓ Selected: {selected_item}")
                return selected_item
            else:
                print(f"❌ Invalid number. Please enter 1-{len(items_data)}")
                continue
        
        # Check if it's an item ID (partial match)
        matches = [(item_id, desc) for item_id, desc in items_data if choice.upper() in item_id.upper()]
        
        if len(matches) == 1:
            print(f"✓ Selected: {matches[0][0]}")
            return matches[0][0]
        elif len(matches) > 1:
            print(f"\n⚠️  Multiple matches found:")
            for i, (item_id, desc) in enumerate(matches, 1):
                desc_short = desc[:50] + "..." if len(desc) > 50 else desc
                print(f"  [{i}] {item_id} - {desc_short}")
            sub_choice = input(f"Select one [1-{len(matches)}]: ").strip()
            if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(matches):
                return matches[int(sub_choice) - 1][0]
        else:
            print(f"❌ Item not found: {choice}")


def save_recent_config(module: str, item_id: str, provider: str, model: str):
    """Save recently used configuration."""
    config_file = Path(__file__).parent.parent / ".recent_config.yaml"
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        # Update recent usage
        config['last_used'] = {
            'module': module,
            'item_id': item_id,
            'provider': provider,
            'model': model,
        }
        
        # Update recent modules (keep last 5)
        recent_modules = config.get('recent_modules', [])
        if module not in recent_modules:
            recent_modules.insert(0, module)
        else:
            recent_modules.remove(module)
            recent_modules.insert(0, module)
        config['recent_modules'] = recent_modules[:5]
        
        # Save
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    except Exception as e:
        # Silently fail if can't save
        pass


def load_recent_config() -> dict:
    """Load recently used configuration."""
    config_file = Path(__file__).parent.parent / ".recent_config.yaml"
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception:
        pass
    
    return {}


def select_start_step() -> int:
    """
    Interactive step selection for resuming workflow.
    
    Returns:
        Selected step number (1-9)
    """
    print("\n┌─ Workflow Starting Point ─────────────────────────────────────────────────┐")
    print("│                                                                            │")
    print("│  [1] 📄 Loading Configuration                                             │")
    print("│      ► Start from beginning (Recommended) ⭐                               │")
    print("│                                                                            │")
    print("│  [2] 🔍 Analyzing Input Files                                             │")
    print("│      ► Parse logs, reports, and constraints                               │")
    print("│                                                                            │")
    print("│  [3] 📝 Generating README                                                 │")
    print("│      ► Create documentation from templates                                │")
    print("│                                                                            │")
    print("│  [4] 💻 Generating Code                                                   │")
    print("│      ► AI-powered checker implementation                                  │")
    print("│                                                                            │")
    print("│  [5] ✅ Self-Check                                                        │")
    print("│      ► Syntax validation and structure check                              │")
    print("│                                                                            │")
    print("│  [6] 🔧 Output Refinement                                                 │")
    print("│      ► Format adjustments and cleanup                                     │")
    print("│                                                                            │")
    print("│  [7] 🎯 Final Review                                                      │")
    print("│      ► Testing and modification loop                                      │")
    print("│                                                                            │")
    print("│  [8] 📊 Archiving Results                                                 │")
    print("│      ► Save artifacts to project folders                                  │")
    print("│                                                                            │")
    print("│  [9] 🏁 Workflow Complete                                                 │")
    print("│      ► Print summary and exit                                             │")
    print("│                                                                            │")
    print("└───────────────────────────────────────────────────────────────────────────┘")
    
    while True:
        choice = input("\nSelect starting step [1-9, default=1] ► ").strip() or "1"
        
        if choice in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            step = int(choice)
            
            # Show what will be skipped
            if step > 1:
                print(f"\nℹ️  Will resume from Step {step}, skipping Steps 1-{step-1}")
                
                # Warning for resuming from middle
                if step >= 4:
                    confirm = input("⚠️  Resuming from middle requires previous artifacts. Continue? [Y/n] ► ").strip().lower()
                    if confirm and confirm != 'y':
                        print("Returning to step selection...\n")
                        continue
            
            return step
        else:
            print("❌ Invalid choice. Please enter a number from 1 to 9")


def interactive_mode() -> dict:
    """
    Run interactive selection for all parameters.
    
    Returns:
        Dict with selected parameters: {provider, model, module, item_id, resume_from_step}
    """
    # Load recent config
    recent_config = load_recent_config()
    recent_modules = recent_config.get('recent_modules', [])
    
    # Print header with progress
    print("\n" + "="*80)
    print("🚀 AutoGenChecker v2.0 - Interactive Mode")
    print("="*80)
    
    # 1. Select LLM Provider
    print("\nStep 1/5: 🤖 LLM Configuration")
    print("─" * 80)
    provider, model = select_llm_provider()
    
    # 2. Discover CHECKLIST root
    try:
        from utils.paths import discover_project_paths
    except ImportError:
        from AutoGenChecker.utils.paths import discover_project_paths
    
    paths = discover_project_paths()
    checklist_root = paths.workspace_root
    
    # 3. Select Module
    print("\n" + "─" * 80)
    print("Step 2/5: 📦 Module Selection")
    print("─" * 80)
    module = select_module(checklist_root, recent_modules)
    
    # 4. Select Item
    print("\n" + "─" * 80)
    print("Step 3/5: 📝 Item Selection")
    print("─" * 80)
    item_id = select_item(checklist_root, module)
    
    # 5. Select Starting Step
    print("\n" + "─" * 80)
    print("Step 4/5: 🔢 Workflow Control")
    print("─" * 80)
    resume_from_step = select_start_step()
    
    # 6. Confirmation
    print("\n" + "─" * 80)
    print("Step 5/5: ✓ Confirmation")
    print("─" * 80)
    print("\n┌─ Configuration Summary ───────────────────────────────────────────────────┐")
    print(f"│  LLM Provider:    {provider:<58} │")
    print(f"│  Model:           {model:<58} │")
    print(f"│  Module:          {module:<58} │")
    print(f"│  Item ID:         {item_id:<58} │")
    print(f"│  Start Step:      {resume_from_step if resume_from_step else 1:<58} │")
    print(f"│  Est. Time:       {'5-10 minutes':<58} │")
    print("└───────────────────────────────────────────────────────────────────────────┘")
    
    confirm = input("\nPress ENTER to start generation, or Ctrl+C to cancel ► ").strip().lower()
    
    if confirm and confirm not in ['', 'y', 'yes']:
        print("❌ Cancelled by user")
        sys.exit(0)
    
    # Save config
    save_recent_config(module, item_id, provider, model)
    
    return {
        'provider': provider,
        'model': model,
        'module': module,
        'item_id': item_id,
        'resume_from_step': resume_from_step if resume_from_step > 1 else None,  # None means start from beginning
    }
