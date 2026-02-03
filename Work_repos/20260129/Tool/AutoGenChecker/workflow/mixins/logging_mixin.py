"""
Logging functionality for IntelligentCheckerAgent.

Provides logging to file and optional Rich terminal output.
"""

from datetime import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class LoggingMixin:
    """Mixin for logging and Rich console functionality."""
    
    def _setup_logging(self) -> None:
        """Setup logging to file for complete history tracking."""
        try:
            from utils.paths import discover_project_paths
        except ImportError:
            from AutoGenChecker.utils.paths import discover_project_paths
        
        paths = discover_project_paths()
        # Use autogen_root for logs (Tool/AutoGenChecker/logs)
        log_dir = paths.autogen_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = log_dir / f"{self.item_id}_{timestamp}.log"
        
        # Setup logger
        self.logger = logging.getLogger(f"Agent_{self.item_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler - captures everything
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        self.logger.info(f"="*80)
        self.logger.info(f"Agent initialized for {self.item_id}")
        self.logger.info(f"Module: {self.module}")
        self.logger.info(f"LLM: {self.llm_provider}/{self.llm_model}")
        self.logger.info(f"="*80)
    
    def _setup_rich_console(self) -> None:
        """Setup Rich console for beautiful terminal output."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.progress import Progress
            from rich.table import Table
            self.console = Console()
            self.use_rich = True
        except ImportError:
            self.console = None
            self.use_rich = False
            if self.verbose:
                print("💡 Tip: Install 'rich' for better terminal output: pip install rich")
    
    def _log(self, message: str, level: str = "INFO", emoji: str = "") -> None:
        """
        Log message to both file and terminal.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            emoji: Optional emoji prefix for terminal display
        """
        # Log to file (always)
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
        
        # Display in terminal (if verbose)
        if self.verbose:
            display_msg = f"{emoji} {message}" if emoji else message
            print(display_msg)
    
    def _print_final_summary(self, artifacts: dict, check_results: dict) -> None:
        """Print final summary of the generation process."""
        print("\n┌─ Generation Complete! 🎉 ────────────────────────────────────────────────┐")
        
        # Count statistics
        readme_lines = len(artifacts.readme.split('\n')) if artifacts.readme else 0
        code_lines = len(artifacts.code.split('\n')) if artifacts.code else 0
        has_issues = check_results.get('has_issues', False)
        check_count = len(check_results.get('results', []))
        
        print("│                                                                            │")
        print("│  Component         Status              Details                            │")
        print("├────────────────────┼───────────────────┼────────────────────────────────┤")
        print(f"│  README            │ {'✅ Generated' if readme_lines > 0 else '❌ Missing':<17} │ {readme_lines} lines{' '*25} │")
        print(f"│  Code              │ {'✅ Generated' if code_lines > 0 else '❌ Missing':<17} │ {code_lines} lines{' '*25} │")
        print(f"│  Self-Check        │ {'✅ Passed' if not has_issues else '❌ Has Issues':<17} │ {check_count} checks{' '*25} │")
        print(f"│  Log File          │ 📝 Saved{' '*9} │ {str(self.log_file.name):<30} │")
        print("└────────────────────┴───────────────────┴────────────────────────────────┘")
        
        print("\n┌─ Next Steps ──────────────────────────────────────────────────────────────┐")
        print("│  1. Review generated README and code                                      │")
        print("│  2. Run tests to validate functionality                                   │")
        print("│  3. Use [R]eset if regeneration needed                                    │")
        print("│  4. Use [F]inalize when satisfied with results                            │")
        print("└───────────────────────────────────────────────────────────────────────────┘")
        
        self._log(f"Log saved to: {self.log_file}", "INFO", "📝")

