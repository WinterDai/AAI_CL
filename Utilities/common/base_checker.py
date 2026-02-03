#!/usr/bin/env python3
################################################################################
# Script Name: base_checker.py
#
# Purpose:
#   Base class for all checker scripts providing common functionality:
#   - Path initialization (logs, reports)
#   - File reading utilities
#   - Configuration loading
#   - Output formatting setup
#
# Usage:
#   from base_checker import BaseChecker
#   
#   class MyChecker(BaseChecker):
#       def __init__(self):
#           super().__init__(
#               check_module="5.0_SYNTHESIS_CHECK",
#               item_id="IMP-5-0-0-XX",
#               item_desc="Check description"
#           )
#       
#       def execute_check(self):
#           # Implement check logic here
#           pass
#       
#       def run(self):
#           self.init_checker()
#           result = self.execute_check()
#           self.write_output(result)
#
# Author: yyin
# Date: 2025-10-31
################################################################################


class ConfigurationError(Exception):
    """
    Exception raised when configuration is invalid or missing.
    
    This exception carries a CheckResult object for immediate return.
    """
    def __init__(self, check_result):
        self.check_result = check_result
        super().__init__("Configuration error detected")

from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from parse_interface import load_item_data, find_input_files
from config_reader import detect_project_root
from output_formatter import OutputFormatter, CheckResult
from result_cache_manager import get_global_cache


class BaseChecker:
    """
    Base class for all checker scripts.
    
    Provides common functionality:
    - Project root detection
    - Output path initialization (logs, reports)
    - File reading utilities
    - Configuration loading (item_data from DATA_INTERFACE)
    - Output formatter setup
    
    Subclasses should:
    1. Call super().__init__() with check_module, item_id, item_desc
    2. Call init_checker() to initialize paths and load config
    3. Implement execute_check() with specific check logic
    4. Call write_output() to generate log and report
    """
    
    # DEPRECATED: Use result_cache_manager.get_global_cache() instead
    # Kept for backward compatibility
    _result_cache: Dict[str, CheckResult] = {}
    
    def __init__(self, check_module: str, item_id: str, item_desc: str):
        """
        Initialize base checker.
        
        Args:
            check_module: Module name (e.g., '5.0_SYNTHESIS_CHECK')
            item_id: Item ID (e.g., 'IMP-5-0-0-00')
            item_desc: Item description (e.g., 'Confirm synthesis is using lib models for timing?')
        """
        self.check_module = check_module
        self.item_id = item_id
        self.item_desc = item_desc
        
        # Will be initialized by init_checker()
        self.root: Optional[Path] = None
        self.log_path: Optional[Path] = None
        self.rpt_path: Optional[Path] = None
        self.cache_dir: Optional[Path] = None
        self.formatter: Optional[OutputFormatter] = None
        self.item_data: Optional[Dict[str, Any]] = None
    
    def init_checker(self, script_path: Optional[Path] = None):
        """
        Initialize checker: detect root, setup paths, load config.
        
        Args:
            script_path: Path to the checker script file. If None, uses __file__ from caller.
        
        This method:
        1. Detects project root
        2. Initializes log and report paths
        3. Truncates existing files
        4. Initializes OutputFormatter
        5. Loads item configuration from DATA_INTERFACE
        """
        # 1. Detect project root
        if script_path is None:
            # Try to get from caller's context
            import inspect
            frame = inspect.currentframe().f_back
            script_path = Path(frame.f_globals['__file__'])
        
        self.root = detect_project_root(script_path.parent)
        
        # 2. Initialize output paths
        module_dir = self.root / 'Check_modules' / self.check_module
        logs = module_dir / 'logs'
        reports = module_dir / 'reports'
        outputs = module_dir / 'outputs'
        cache_dir = outputs / '.cache'
        
        logs.mkdir(parents=True, exist_ok=True)
        reports.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_path = logs / f'{self.item_id}.log'
        self.rpt_path = reports / f'{self.item_id}.rpt'
        self.cache_dir = cache_dir  # Store cache directory for later use
        
        # 3. Truncate existing files
        self.log_path.write_text('', encoding='utf-8')
        self.rpt_path.write_text('', encoding='utf-8')
        
        # 4. Initialize formatter
        self.formatter = OutputFormatter(self.item_id, self.item_desc)
        
        # 5. Load item configuration
        self.item_data = load_item_data(self.check_module, self.item_id)
    
    def get_input_file(self, filename: str) -> Tuple[Optional[Path], str, str]:
        """
        Get input file path from DATA_INTERFACE.
        
        Args:
            filename: Name of the input file to find (e.g., 'qor.rpt', 'sdc.rpt')
        
        Returns:
            Tuple of (file_path, log_error_message, report_error_message)
            - file_path: Path object if found, None if not found
            - log_error_message: Error message for log file
            - report_error_message: Error message for report file
        """
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        return find_input_files(self.root, self.check_module, self.item_id, filename)
    
    def read_file(self, path: Path) -> Optional[List[str]]:
        """
        Read text file and return lines.
        
        Args:
            path: Path to the file to read
        
        Returns:
            List of lines (stripped of newlines) or None if error
        """
        try:
            return path.read_text(encoding='utf-8', errors='ignore').splitlines()
        except Exception:
            return None
    
    def validate_input_files(self, raise_on_empty: bool = True) -> Tuple[List[Path], List[str]]:
        """
        Validate all input files from configuration.
        
        Args:
            raise_on_empty: If True, raises ConfigurationError when input_files is empty/missing.
                          If False, returns ([], []) for backward compatibility.
        
        Returns:
            Tuple of (valid_files, missing_files)
            - valid_files: List of Path objects that exist and are readable
            - missing_files: List of file path strings that are missing or unreadable
        
        Raises:
            ConfigurationError: When input_files is empty/missing and raise_on_empty=True
            
        Note:
            Set raise_on_empty=False for backward compatibility with old checkers.
        """
        if self.item_data is None or 'input_files' not in self.item_data:
            if raise_on_empty:
                error_msg = "input_files not configured in YAML"
                raise ConfigurationError(self.create_config_error(error_msg))
            return ([], [])
        
        input_files = self.item_data['input_files']
        
        # If input_files is empty list or None, raise error or return empty
        if not input_files:
            if raise_on_empty:
                error_msg = "input_files is empty in YAML configuration"
                raise ConfigurationError(self.create_config_error(error_msg))
            return ([], [])
        
        if isinstance(input_files, str):
            input_files = [input_files]
        
        # Expand ${CHECKLIST_ROOT} variables to absolute paths
        from parse_interface import expand_variables, get_builtin_variables
        variables = get_builtin_variables()
        expanded_files = expand_variables(input_files, variables)
        
        valid_files = []
        missing_files = []
        
        import glob
        
        for file_path_str in expanded_files:
            # Check if path contains wildcards
            if '*' in file_path_str or '?' in file_path_str:
                # Use glob to find matching files
                matching_files = glob.glob(file_path_str)
                
                if not matching_files:
                    missing_files.append(f"{file_path_str} (no files match wildcard pattern)")
                else:
                    # Add all matching files to valid_files
                    for matched_file in matching_files:
                        file_path = Path(matched_file)
                        if file_path.is_file():
                            try:
                                # Try to open and read first byte to check readability
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    f.read(1)
                                valid_files.append(file_path)
                            except Exception as e:
                                missing_files.append(f"{str(file_path)} (unreadable: {str(e)})")
            else:
                # No wildcards - normal file path
                file_path = Path(file_path_str)
                
                # Check if file exists and is readable
                if not file_path.exists():
                    missing_files.append(str(file_path))
                elif not file_path.is_file():
                    missing_files.append(f"{str(file_path)} (not a file)")
                else:
                    try:
                        # Try to open and read first byte to check readability
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.read(1)
                        valid_files.append(file_path)
                    except Exception as e:
                        missing_files.append(f"{str(file_path)} (unreadable: {str(e)})")
        
        return (valid_files, missing_files)
    
    def create_config_error(self, error_message: str) -> CheckResult:
        """
        Create error result for configuration errors.
        
        This is a common error handler for configuration issues like:
        - Empty input_files when files are required
        - Missing required configuration fields
        - Invalid configuration values
        
        Args:
            error_message: Description of the configuration error
        
        Returns:
            CheckResult with CONFIG_ERROR status
        """
        from output_formatter import DetailItem, Severity, create_check_result
        
        # Use error_message as the name so it matches with items list
        details = [DetailItem(
            severity=Severity.FAIL,
            name=error_message,
            line_number=0,
            file_path="",
            reason=error_message
        )]
        
        return create_check_result(
            value="CONFIG_ERROR",
            is_pass=False,
            has_pattern_items=self.has_pattern_items(),
            has_waiver_value=self.has_waiver_value(),
            details=details,
            error_groups={
                "ERROR01": {
                    "description": "Configuration error",
                    "items": [error_message]  # Must match detail.name
                }
            },
            item_desc=self.item_desc
        )
    
    def create_missing_files_error(self, missing_files: List[str]) -> Optional[CheckResult]:
        """
        Create error result for missing or unreadable input files.
        
        This is a common error handler that all checkers can use to report
        configuration errors when input files are missing or unreadable.
        
        Args:
            missing_files: List of missing file paths
        
        Returns:
            CheckResult with error details if files are missing, None otherwise
        """
        if not missing_files:
            return None
        
        # Import here to avoid circular dependency
        from output_formatter import DetailItem, Severity, create_check_result
        
        # Get waive items to pass to create_check_result
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        details = []
        for missing_file in missing_files:
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=missing_file,
                line_number=0,
                file_path="N/A",
                reason="Input file not found or unreadable - check configuration"
            ))
        
        return create_check_result(
            value=0,
            is_pass=False,
            has_pattern_items=self.has_pattern_items(),
            has_waiver_value=self.has_waiver_value(),
            details=details,
            item_desc=self.item_desc,
            error_groups={
                "ERROR01": {
                    "description": "Missing or unreadable input files - configuration error",
                    "items": missing_files
                }
            }
        )
    
    def get_requirements(self) -> Dict[str, Any]:
        """
        Get requirements configuration from item_data.
        
        Returns:
            Dictionary containing requirements config (value, pattern_items, etc.)
        """
        if self.item_data is None:
            return {}
        return self.item_data.get('requirements', {})
    
    def get_waivers(self) -> Dict[str, Any]:
        """
        Get waiver configuration from item_data.
        
        Returns:
            Dictionary containing waiver config (value, waive_items, etc.)
        """
        if self.item_data is None:
            return {}
        return self.item_data.get('waivers', {})
    
    def get_pattern_items(self) -> List[str]:
        """
        Get pattern_items from requirements.
        
        Returns:
            List of pattern items (expected values)
        """
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', [])
        return [str(item).strip() for item in pattern_items]
    
    def get_waive_items(self) -> List[str]:
        """
        Get waive_items from waivers.
        Supports format: "module_name, # reason" - extracts only module_name before comma.
        
        Returns:
            List of waive items (items to be waived, without reasons)
        """
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', [])
        
        result = []
        for item in waive_items:
            item_str = str(item).strip()
            # If item contains comma, take only the part before comma
            # Format: "module_name, # reason" → "module_name"
            if ',' in item_str:
                item_str = item_str.split(',')[0].strip()
            result.append(item_str)
        
        return result
    
    def get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Get waive_items with their reasons from waivers.
        
        Supports multiple formats:
        - Dict format: {"name": "pattern", "reason": "text"}
        - String with semicolon: "module_name ; # reason"
        - String with comma: "module_name, # reason"
        - Plain string: "module_name" (no reason)
        
        Returns:
            Dictionary mapping waive item to its reason
            Format: {"module_name": "reason"}
        """
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', [])
        
        result = {}
        for item in waive_items:
            # Handle dict format (new format)
            if isinstance(item, dict):
                name = item.get('name', '').strip()
                reason = item.get('reason', '').strip()
                if name:
                    result[name] = reason
                continue
            
            # Handle string formats (legacy)
            item_str = str(item).strip()
            # Support both comma and semicolon separators
            # Format: "module_name, # reason" or "module_name ; # reason"
            if ';' in item_str:
                # Semicolon separator
                parts = item_str.split(';', 1)
                name = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                # Remove leading # from reason if present
                if reason.startswith('#'):
                    reason = reason[1:].strip()
                result[name] = reason
            elif ',' in item_str:
                # Comma separator (legacy format)
                parts = item_str.split(',', 1)
                name = parts[0].strip()
                reason = parts[1].strip() if len(parts) > 1 else ""
                # Remove leading # from reason if present
                if reason.startswith('#'):
                    reason = reason[1:].strip()
                result[name] = reason
            else:
                # No separator - no reason provided
                result[item_str] = ""
        
        return result
    
    def get_waive_items_raw(self) -> Dict[str, str]:
        """
        Get raw waive_items mapping from name to original string (for log output).
        
        Supports multiple formats:
        - Dict format: {"name": "pattern", "reason": "text"}
        - String with semicolon/comma: "module_name ; # reason"
        - Plain string: "module_name"
        
        Returns:
            Dictionary mapping waive item name to original string
            Format: {"module_name": "module_name, # reason"} or {"module_name": "module_name ; # reason"}
        """
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', [])
        
        result = {}
        for item in waive_items:
            # Handle dict format
            if isinstance(item, dict):
                name = item.get('name', '').strip()
                reason = item.get('reason', '').strip()
                if name:
                    # Format as "name ; # reason" for consistency
                    result[name] = f"{name} ; # {reason}" if reason else name
                continue
            
            # Handle string formats
            item_str = str(item).strip()
            # Extract name (part before comma or semicolon)
            if ';' in item_str:
                name = item_str.split(';')[0].strip()
            elif ',' in item_str:
                name = item_str.split(',')[0].strip()
            else:
                name = item_str
            # Map name to original string
            result[name] = item_str
        
        return result
    
    def has_pattern_items(self) -> bool:
        """Check if pattern_items are defined."""
        return bool(self.get_pattern_items())
    
    def has_waiver_value(self) -> bool:
        """Check if waiver value is defined (not None or N/A)."""
        waivers = self.get_waivers()
        waiver_value = waivers.get('value')
        return waiver_value not in [None, 'N/A']
    
    def detect_checker_type(self, custom_requirements: Optional[Dict[str, Any]] = None) -> int:
        """
        Auto-detect checker type based on configuration.
        
        Type Detection Logic:
        - Type 1: requirements.value=N/A AND waivers.value=N/A/0 (Boolean check, no waiver)
        - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0 (Value comparison, no waiver)
        - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0 (Value + waiver logic)
        - Type 4: requirements.value=N/A AND waivers.value>0 (Boolean + waiver logic)
        
        Args:
            custom_requirements: Optional custom requirements dict (for cross-reference cases).
                                If None, uses self.get_requirements()
        
        Returns:
            1: Type 1 (Boolean check, no waiver logic)
            2: Type 2 (Value comparison, no waiver)
            3: Type 3 (Value comparison WITH waiver logic)
            4: Type 4 (Boolean WITH waiver logic)
        """
        # Get requirements (allow custom for cross-reference cases)
        if custom_requirements is not None:
            requirements = custom_requirements
        else:
            requirements = self.get_requirements()
        
        req_value = requirements.get('value', 'N/A') if requirements else 'N/A'
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        # Get waivers (always from self)
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # Check if has waiver logic
        has_waiver_logic = False
        if waiver_value != 'N/A':
            try:
                has_waiver_logic = (float(waiver_value) > 0)
            except (ValueError, TypeError):
                pass
        
        # Check if has value requirement
        has_value_requirement = False
        if req_value != 'N/A':
            try:
                has_value_requirement = (float(req_value) >= 0 and len(pattern_items) > 0)
            except (ValueError, TypeError):
                pass
        
        # Determine type
        if has_value_requirement and has_waiver_logic:
            return 3  # Type 3: Value + Waiver Logic
        elif has_value_requirement:
            return 2  # Type 2: Value only
        elif has_waiver_logic:
            return 4  # Type 4: Boolean + Waiver Logic
        else:
            return 1  # Type 1: Boolean only
    
    def write_output(self, result: CheckResult):
        """
        Write check result to log and report files.
        Also cache the result in memory for faster YAML generation.
        
        Args:
            result: CheckResult object containing check results
        """
        if self.formatter is None or self.log_path is None or self.rpt_path is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        self.formatter.write_log(result, self.log_path, mode='w')
        self.formatter.write_report(result, self.rpt_path, mode='w')
        
        # Cache result using new cache manager
        # This handles Redis (if available) + memory + file cache automatically
        # File cache is stored in outputs/.cache/ directory
        from result_cache_manager import configure_global_cache
        cache = configure_global_cache(
            cache_dir=self.cache_dir,
            max_memory_size=200,
            enable_file_cache=True
        )
        cache.set(self.item_id, result)
        
        # DEPRECATED: Keep for backward compatibility
        BaseChecker._result_cache[self.item_id] = result
    
    @classmethod
    def get_cached_result(cls, item_id: str) -> Optional[CheckResult]:
        """
        Get cached CheckResult for an item.
        
        Uses new ResultCacheManager with L1 (memory) + L2 (file) caching.
        
        Args:
            item_id: Item ID to retrieve
            
        Returns:
            CheckResult if cached, None otherwise
        """
        # Try new cache manager first (supports file cache)
        cache = get_global_cache()
        result = cache.get(item_id)
        if result:
            return result
        
        # DEPRECATED: Fallback to old cache for backward compatibility
        return cls._result_cache.get(item_id)
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached results (both old and new cache)."""
        cache = get_global_cache()
        cache.clear_all()
        cls._result_cache.clear()
    
    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        cache = get_global_cache()
        return cache.get_stats()
    
    @classmethod
    def print_cache_stats(cls):
        """Print cache performance statistics."""
        cache = get_global_cache()
        cache.print_stats()
    
    def execute_check(self) -> CheckResult:
        """
        Execute the check logic.
        
        This method should be overridden by subclasses to implement
        specific check logic.
        
        Returns:
            CheckResult object containing check results
        
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute_check() method"
        )
    
    def run(self):
        """
        Main execution method.
        
        Default implementation:
        1. Initialize checker (paths, config)
        2. Execute check logic (calls execute_check())
        3. Write output (log and report)
        
        Can be overridden by subclasses for custom flow.
        """
        self.init_checker()
        result = self.execute_check()
        self.write_output(result)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == '__main__':
    # This is an example showing how to use BaseChecker
    # Real checkers should be in separate files
    
    from output_formatter import create_check_result, DetailItem, Severity
    
    class ExampleChecker(BaseChecker):
        """Example checker implementation."""
        
        def __init__(self):
            super().__init__(
                check_module="5.0_SYNTHESIS_CHECK",
                item_id="IMP-5-0-0-EXAMPLE",
                item_desc="Example checker description"
            )
        
        def execute_check(self) -> CheckResult:
            """Implement check logic."""
            # Example: Simple pass result
            details = [
                DetailItem(
                    severity=Severity.INFO,
                    name="Example item",
                    line_number=1,
                    file_path="example.txt",
                    reason="Example check passed."
                )
            ]
            
            return create_check_result(
                value=1,
                is_pass=True,
                has_pattern_items=self.has_pattern_items(),
                has_waiver_value=self.has_waiver_value(),
                details=details
            )
    
    # Run example checker
    # checker = ExampleChecker()
    # checker.run()
    print("BaseChecker module loaded successfully.")
    print("Use: from base_checker import BaseChecker")
