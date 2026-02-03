"""
Input File Parser Template - Reusable Mixin for Parsing Input Files

This module provides a comprehensive, reusable mixin class for parsing various types of input files
(logs, reports, timing reports, QoR files, etc.).
Extracted and generalized from multiple proven checkers:
- IMP-10-0-0-10: Pattern matching and file path extraction
- IMP-5-0-0-01: File reference extraction (.lef, .tlef)
- IMP-5-0-0-02: Multi-stage chain extraction (domain→rc_corner→qrc_tech)
- IMP-5-0-0-05: Section-based parsing (Check Design Report)
- IMP-5-0-0-07: Structured block extraction (create_delay_corner)
- IMP-6-0-0-02: Simple list extraction
- IMP-13-0-0-00: Command extraction

Supported Parsing Patterns:
1. Simple pattern matching (keywords, regex)
2. File reference extraction (.lef, .rpt, .tarpt, etc.)
3. Section-based parsing (between markers)
4. Block-based parsing (command blocks)
5. Multi-stage chain extraction
6. Count/metric extraction
7. Violation/error extraction

Usage Examples:

    # Pattern 1: Simple keyword/regex matching
    result = self.parse_log_with_patterns(
        log_file, {'in2out': r'_(in2out)_|timing_in2out'}
    )
    
    # Pattern 2: Extract file references
    files = self.extract_file_references(
        log_file, extensions=['.lef', '.tlef']
    )
    
    # Pattern 3: Parse structured sections
    violations = self.parse_section(
        log_file,
        start_marker=r'Check Design Report',
        end_marker=r'Total number',
        item_pattern=r'hinst:\\s*(\\S+)'
    )
    
    # Pattern 4: Extract command blocks
    blocks = self.extract_command_blocks(
        log_file,
        command='create_delay_corner'
    )
    
    # Pattern 5: Count occurrences
    count = self.count_pattern(
        log_file,
        pattern=r'ERROR:'
    )

Author: yyin
Date: 2025-12-08
Version: 2.0.0
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set


class InputFileParserMixin:
    """
    Comprehensive mixin class for parsing various input file formats.
    
    Covers multiple parsing scenarios:
    - Pattern-based keyword/phrase matching
    - File reference extraction (any extension)
    - Section-based parsing (content between markers)
    - Block-based parsing (command blocks with parameters)
    - Multi-stage chain extraction
    - Count and metric extraction
    - Violation and error detection
    
    All methods are battle-tested from production checkers.
    """
    
    # =========================================================================
    # Pattern 1: Simple Pattern Matching (from IMP-10-0-0-10)
    # =========================================================================
    
    def parse_log_with_patterns(
        self,
        log_file: Path,
        patterns: Dict[str, str],
        required_items: Optional[List[str]] = None,
        extract_paths: bool = True,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Parse log file using regex patterns to find required items.
        
        Args:
            log_file: Path to the log file to parse
            patterns: Dict mapping item names to regex patterns
                     Example: {'in2out': r'_(in2out)_|timing_in2out'}
            required_items: List of item names that must be found (default: all pattern keys)
            extract_paths: Whether to extract file paths from matched lines (default: True)
            case_sensitive: Whether pattern matching is case-sensitive (default: False)
        
        Returns:
            Dict with structure:
            {
                'found': {
                    'item_name': {
                        'line_number': int,
                        'file_path': str,
                        'line_content': str,
                        'extracted_path': str  # if extract_paths=True
                    }
                },
                'missing': ['item1', 'item2'],
                'log_file': str,
                'total_items': int,
                'found_count': int,
                'missing_count': int
            }
        
        Example:
            patterns = {
                'in2out': r'_(in2out)_|timing_in2out',
                'in2reg': r'_(in2reg)_|timing_in2reg'
            }
            result = self.parse_log_with_patterns(log_file, patterns)
            # result['found']['in2out']['extracted_path'] = 'reports/.../timing_in2out.rpt'
        """
        if required_items is None:
            required_items = list(patterns.keys())
        
        found = {}
        flags = 0 if case_sensitive else re.IGNORECASE
        
        # Read log file (use BaseChecker's read_file method if available)
        if hasattr(self, 'read_file'):
            # Handle both Path and str
            from pathlib import Path
            log_path = Path(log_file) if not isinstance(log_file, Path) else log_file
            lines = self.read_file(log_path)
            if lines is None:
                lines = []
        else:
            with open(str(log_file), 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        # Search for each pattern
        for line_num, line in enumerate(lines, 1):
            for item_name, pattern in patterns.items():
                # Skip if already found
                if item_name in found:
                    continue
                
                # Try to match pattern
                if re.search(pattern, line, flags):
                    metadata = {
                        'line_number': line_num,
                        'file_path': str(log_file),
                        'line_content': line.strip()
                    }
                    
                    # Extract file path if requested
                    if extract_paths:
                        extracted = self._extract_file_path_from_line(line)
                        metadata['extracted_path'] = extracted
                    
                    found[item_name] = metadata
        
        # Determine missing items
        missing = [item for item in required_items if item not in found]
        
        return {
            'found': found,
            'missing': missing,
            'log_file': str(log_file),
            'total_items': len(required_items),
            'found_count': len(found),
            'missing_count': len(missing)
        }
    
    def _extract_file_path_from_line(self, line: str) -> str:
        """
        Extract file path from a log line.
        
        Supports multiple formats:
        1. After '>' character: "command > /path/to/file.rpt"
        2. After ':' character: "Writing: /path/to/file.rpt"
        3. Quoted paths: "path/to/file.rpt" or 'path/to/file.rpt'
        4. Common file extensions: .rpt, .log, .tarpt, .gz, etc.
        
        Args:
            line: Log line to extract from
        
        Returns:
            Extracted file path, or empty string if not found
        
        Example:
            line = "<CMD> report_timing > reports/func/timing_in2out.tarpt.gz"
            result = self._extract_file_path_from_line(line)
            # result = "reports/func/timing_in2out.tarpt.gz"
        """
        line = line.strip()
        
        # Method 1: Extract after '>' (most common in timing reports)
        if '>' in line:
            parts = line.split('>')
            if len(parts) > 1:
                path = parts[-1].strip()
                # Remove trailing quotes if present
                path = path.strip('"\'')
                if path:
                    return path
        
        # Method 2: Extract after ':' (common in log messages)
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) > 1:
                potential_path = parts[-1].strip()
                # Check if it looks like a file path
                if '/' in potential_path or '\\' in potential_path:
                    # Extract just the path part
                    path = potential_path.split()[0] if ' ' in potential_path else potential_path
                    path = path.strip('"\'')
                    if self._looks_like_file_path(path):
                        return path
        
        # Method 3: Find quoted paths
        quoted_match = re.search(r'["\']([^"\']+\.[a-z]+)["\']', line, re.IGNORECASE)
        if quoted_match:
            return quoted_match.group(1)
        
        # Method 4: Find paths with common file extensions
        ext_pattern = r'(\S+\.(?:rpt|log|tarpt|gz|yaml|json|txt|csv))'
        ext_match = re.search(ext_pattern, line, re.IGNORECASE)
        if ext_match:
            return ext_match.group(1)
        
        return ''
    
    def _looks_like_file_path(self, text: str) -> bool:
        """
        Check if a string looks like a file path.
        
        Args:
            text: String to check
        
        Returns:
            True if text appears to be a file path
        """
        # Check for path separators
        if '/' not in text and '\\' not in text:
            return False
        
        # Check for common file extensions
        common_exts = ['.rpt', '.log', '.tarpt', '.gz', '.yaml', '.json', '.txt', '.csv']
        if any(text.lower().endswith(ext) for ext in common_exts):
            return True
        
        # Check if it has at least one path component
        parts = text.replace('\\', '/').split('/')
        if len(parts) > 1:
            return True
        
        return False
    
    # =========================================================================
    # Utility: Command/Text Normalization
    # =========================================================================
    
    def normalize_command(self, cmd: str) -> str:
        """
        Normalize command format for consistent matching.
        
        Normalization steps:
        - Remove extra spaces around braces: { CLOCK } → {CLOCK}
        - Normalize multiple spaces to single space
        - Strip leading/trailing whitespace
        
        Args:
            cmd: Raw command string
            
        Returns:
            Normalized command string
        
        Example:
            >>> normalize_command("set_clock_uncertainty 0.02 -hold -from [get_clocks { PHASE_ALIGN_CLOCK}]")
            "set_clock_uncertainty 0.02 -hold -from [get_clocks {PHASE_ALIGN_CLOCK}]"
        """
        # Remove extra spaces around clock names in braces
        # "{ PHASE_ALIGN_CLOCK}" → "{PHASE_ALIGN_CLOCK}"
        normalized = re.sub(r'\{\s+', r'{', cmd)
        normalized = re.sub(r'\s+\}', r'}', normalized)
        
        # Normalize multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def parse_log_with_keywords(
        self,
        log_file: Path,
        keywords: List[str],
        context_lines: int = 0,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Parse log file to find lines containing specific keywords.
        
        Simpler alternative to parse_log_with_patterns for exact keyword matching.
        
        Args:
            log_file: Path to log file
            keywords: List of keywords to search for
            context_lines: Number of context lines to include before/after match
            case_sensitive: Whether matching is case-sensitive
        
        Returns:
            Dict with structure:
            {
                'matches': {
                    'keyword1': [
                        {
                            'line_number': int,
                            'line_content': str,
                            'context_before': [str, ...],
                            'context_after': [str, ...]
                        }
                    ]
                },
                'total_matches': int
            }
        """
        # Read lines
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        matches = {kw: [] for kw in keywords}
        total_matches = 0
        
        for line_num, line in enumerate(lines, 1):
            line_to_check = line if case_sensitive else line.lower()
            
            for keyword in keywords:
                kw_to_check = keyword if case_sensitive else keyword.lower()
                
                if kw_to_check in line_to_check:
                    # Collect context
                    context_before = []
                    context_after = []
                    
                    if context_lines > 0:
                        # Get lines before (index is 0-based)
                        start = max(0, line_num - 1 - context_lines)
                        context_before = lines[start:line_num - 1]
                        
                        # Get lines after
                        end = min(len(lines), line_num + context_lines)
                        context_after = lines[line_num:end]
                    
                    matches[keyword].append({
                        'line_number': line_num,
                        'line_content': line.strip(),
                        'context_before': context_before,
                        'context_after': context_after
                    })
                    total_matches += 1
        
        return {
            'matches': matches,
            'total_matches': total_matches,
            'log_file': str(log_file)
        }
    
    def extract_metrics_from_log(
        self,
        log_file: Path,
        metric_patterns: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract numeric metrics from log file using regex patterns.
        
        Useful for checkers that need to extract timing values, counts, etc.
        
        Args:
            log_file: Path to log file
            metric_patterns: Dict mapping metric names to regex patterns
                           Pattern should have a capture group for the value
                           Example: {'setup_slack': r'Setup Slack:\\s+(-?\\d+\\.?\\d*)'}
        
        Returns:
            Dict with structure:
            {
                'metrics': {
                    'metric_name': {
                        'value': float or str,
                        'line_number': int,
                        'line_content': str
                    }
                },
                'missing_metrics': [str, ...]
            }
        
        Example:
            patterns = {
                'setup_slack': r'Setup Slack:\\s+(-?\\d+\\.?\\d*)',
                'hold_slack': r'Hold Slack:\\s+(-?\\d+\\.?\\d*)'
            }
            result = self.extract_metrics_from_log(log_file, patterns)
            # result['metrics']['setup_slack']['value'] = -0.123
        """
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        metrics = {}
        
        for line_num, line in enumerate(lines, 1):
            for metric_name, pattern in metric_patterns.items():
                if metric_name in metrics:
                    continue
                
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value_str = match.group(1)
                    
                    # Try to convert to float
                    try:
                        value = float(value_str)
                    except (ValueError, TypeError):
                        value = value_str
                    
                    metrics[metric_name] = {
                        'value': value,
                        'line_number': line_num,
                        'line_content': line.strip()
                    }
        
        missing_metrics = [m for m in metric_patterns.keys() if m not in metrics]
        
        return {
            'metrics': metrics,
            'missing_metrics': missing_metrics,
            'log_file': str(log_file)
        }
    
    # =========================================================================
    # Pattern 2: File Reference Extraction (from IMP-5-0-0-01, IMP-5-0-0-02)
    # =========================================================================
    
    def extract_file_references(
        self,
        log_file: Path,
        extensions: Optional[List[str]] = None,
        custom_pattern: Optional[str] = None,
        include_line_info: bool = True
    ) -> Dict[str, Any]:
        """
        Extract file references from log (e.g., .lef, .tlef, .qrc, .lib files).
        
        Covers use cases like:
        - LEF file extraction (IMP-5-0-0-01)
        - QRC tech file extraction (IMP-5-0-0-02)
        - Library file references
        
        Args:
            log_file: Path to log file
            extensions: List of file extensions to search for (e.g., ['.lef', '.tlef'])
                       If None, extracts all file-like patterns
            custom_pattern: Custom regex pattern (overrides extensions)
            include_line_info: Include line numbers and metadata
        
        Returns:
            Dict with structure:
            {
                'files': ['file1.lef', 'file2.tlef', ...],
                'metadata': {
                    'file1.lef': {
                        'line_number': int,
                        'file_path': str,
                        'line_content': str
                    }
                },
                'count': int
            }
        
        Example:
            # Extract all .lef and .tlef files
            result = self.extract_file_references(
                log_file, extensions=['.lef', '.tlef']
            )
            # result['files'] = ['tech.lef', 'macro.tlef', ...]
        """
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        # Build pattern
        if custom_pattern:
            pattern = re.compile(custom_pattern, re.IGNORECASE)
        elif extensions:
            # Create pattern for specified extensions
            ext_list = '|'.join(re.escape(ext.lstrip('.')) for ext in extensions)
            pattern = re.compile(rf'([A-Za-z0-9._/\\-]+\.(?:{ext_list}))', re.IGNORECASE)
        else:
            # Match common file patterns
            pattern = re.compile(r'([A-Za-z0-9._/\\-]+\.[a-z]{2,5})', re.IGNORECASE)
        
        files = []
        seen = set()
        metadata = {}
        
        for line_num, line in enumerate(lines, 1):
            for match in pattern.finditer(line):
                file_ref = match.group(1).strip('[](){}",;')
                
                if file_ref not in seen:
                    seen.add(file_ref)
                    files.append(file_ref)
                    
                    if include_line_info:
                        metadata[file_ref] = {
                            'line_number': line_num,
                            'file_path': str(log_file),
                            'line_content': line.strip()
                        }
        
        return {
            'files': files,
            'metadata': metadata,
            'count': len(files),
            'log_file': str(log_file)
        }
    
    # =========================================================================
    # Pattern 3: Section-Based Parsing (from IMP-5-0-0-05)
    # =========================================================================
    
    def parse_section(
        self,
        log_file: Path,
        start_marker: str,
        end_marker: Optional[str] = None,
        item_pattern: Optional[str] = None,
        stop_on_empty_line: bool = False,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Parse content within a specific section of log file.
        
        Use cases:
        - Extract violations from "Check Design Report" section
        - Parse timing analysis results
        - Extract content between specific markers
        
        Args:
            log_file: Path to log file
            start_marker: Regex pattern marking section start
            end_marker: Regex pattern marking section end (optional)
            item_pattern: Regex pattern to extract items from section
                         Must have at least one capture group
            stop_on_empty_line: Stop parsing at first empty line
            case_sensitive: Whether pattern matching is case-sensitive
        
        Returns:
            Dict with structure:
            {
                'found': True if section was found,
                'items': [extracted items],
                'metadata': {item: {line_number, file_path}},
                'section_start': line number,
                'section_end': line number,
                'section_content': full section text
            }
        
        Example:
            # Extract unresolved references from Check Design Report
            result = self.parse_section(
                log_file,
                start_marker=r'Check Design Report',
                end_marker=r'Total number',
                item_pattern=r'hinst:\\s*(\\S+)'
            )
            # result['items'] = ['ref1', 'ref2', ...]
        """
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        flags = 0 if case_sensitive else re.IGNORECASE
        start_pattern = re.compile(start_marker, flags)
        end_pattern = re.compile(end_marker, flags) if end_marker else None
        item_regex = re.compile(item_pattern, flags) if item_pattern else None
        
        in_section = False
        section_start = None
        section_end = None
        items = []
        metadata = {}
        section_lines = []
        
        for line_num, line in enumerate(lines, 1):
            # Check for section start
            if not in_section and start_pattern.search(line):
                in_section = True
                section_start = line_num
                section_lines.append(line)
                continue
            
            # Inside section
            if in_section:
                # Check for section end
                if end_pattern and end_pattern.search(line):
                    section_end = line_num
                    section_lines.append(line)
                    break
                
                # Stop on empty line if requested
                if stop_on_empty_line and not line.strip():
                    section_end = line_num
                    break
                
                section_lines.append(line)
                
                # Extract items if pattern provided
                if item_regex:
                    matches = item_regex.findall(line)
                    for match in matches:
                        # Handle both single group and multiple groups
                        item = match if isinstance(match, str) else match[0]
                        
                        if item not in metadata:
                            items.append(item)
                            metadata[item] = {
                                'line_number': line_num,
                                'file_path': str(log_file),
                                'line_content': line.strip()
                            }
        
        return {
            'found': section_start is not None,
            'items': items,
            'metadata': metadata,
            'section_start': section_start,
            'section_end': section_end or len(lines),
            'section_content': '\n'.join(section_lines),
            'item_count': len(items)
        }
    
    # =========================================================================
    # Pattern 4: Command Block Extraction (from IMP-5-0-0-02, IMP-5-0-0-07)
    # =========================================================================
    
    def extract_command_blocks(
        self,
        log_file: Path,
        command: str,
        block_delimiter: str = '@',
        extract_params: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured command blocks from log files.
        
        Use cases:
        - Extract create_delay_corner blocks
        - Extract create_rc_corner blocks  
        - Parse multi-line commands with parameters
        
        Args:
            log_file: Path to log file
            command: Command name to search for (e.g., 'create_delay_corner')
            block_delimiter: Character marking end of command block (default: '@')
            extract_params: List of parameter names to extract from blocks
                           e.g., ['-name', '-rc_corner', '-qrc_tech']
        
        Returns:
            Dict with structure:
            {
                'blocks': [
                    {
                        'content': full block text,
                        'line_start': int,
                        'line_end': int,
                        'params': {'-name': 'value', '-rc_corner': 'value'}
                    }
                ],
                'count': int
            }
        
        Example:
            # Extract create_delay_corner blocks with parameters
            result = self.extract_command_blocks(
                log_file,
                command='create_delay_corner',
                extract_params=['-name', '-rc_corner']
            )
            # result['blocks'][0]['params'] = {'-name': 'corner1', '-rc_corner': 'rc1'}
        """
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        content = '\n'.join(lines)
        
        # Extract command blocks
        block_pattern = rf'{re.escape(command)}[^{re.escape(block_delimiter)}]*?(?={re.escape(block_delimiter)}|\Z)'
        blocks_raw = re.findall(block_pattern, content, re.DOTALL | re.IGNORECASE)
        
        blocks = []
        for block_content in blocks_raw:
            block_info = {
                'content': block_content.strip(),
                'line_start': self._find_line_number(lines, block_content[:50]),
                'line_end': 0,
                'params': {}
            }
            
            # Extract parameters if requested
            if extract_params:
                for param in extract_params:
                    param_pattern = rf'{re.escape(param)}\s+(\S+)'
                    match = re.search(param_pattern, block_content)
                    if match:
                        block_info['params'][param] = match.group(1)
            
            blocks.append(block_info)
        
        return {
            'blocks': blocks,
            'count': len(blocks),
            'log_file': str(log_file)
        }
    
    def _find_line_number(self, lines: List[str], text_snippet: str) -> int:
        """Find line number containing text snippet."""
        for line_num, line in enumerate(lines, 1):
            if text_snippet in line:
                return line_num
        return 0
    
    # =========================================================================
    # Pattern 5: Simple Count/Occurrence Detection
    # =========================================================================
    
    def count_pattern(
        self,
        log_file: Path,
        pattern: str,
        case_sensitive: bool = False,
        return_matches: bool = False
    ) -> Dict[str, Any]:
        """
        Count occurrences of a pattern in log file.
        
        Use cases:
        - Count ERROR messages
        - Count WARNING messages
        - Count specific violations
        
        Args:
            log_file: Path to log file
            pattern: Regex pattern to count
            case_sensitive: Whether matching is case-sensitive
            return_matches: Return list of matching lines
        
        Returns:
            Dict with structure:
            {
                'count': int,
                'matches': [{'line_number': int, 'line': str}] if return_matches
            }
        
        Example:
            # Count ERROR messages
            result = self.count_pattern(log_file, r'ERROR:', return_matches=True)
            # result['count'] = 5
            # result['matches'] = [{'line_number': 10, 'line': 'ERROR: ...'}]
        """
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        count = 0
        matches = []
        
        for line_num, line in enumerate(lines, 1):
            if regex.search(line):
                count += 1
                if return_matches:
                    matches.append({
                        'line_number': line_num,
                        'line': line.strip(),
                        'file_path': str(log_file)
                    })
        
        result = {'count': count, 'log_file': str(log_file)}
        if return_matches:
            result['matches'] = matches
        
        return result
    
    # =========================================================================
    # Pattern 6: Multi-Stage Chain Extraction (from IMP-5-0-0-02)
    # =========================================================================
    
    def extract_chain(
        self,
        log_files: List[Path],
        chain_spec: List[Dict[str, Any]],
        initial_values: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract data through multi-stage chain (e.g., domain → rc_corner → qrc_tech).
        
        Use case: IMP-5-0-0-02 - Extract QRC files through domain→rc_corner→qrc_tech
        
        Args:
            log_files: List of log files to search
            chain_spec: List of extraction specs for each stage
                [{
                    'search_for': 'domain',  # What to search for
                    'in_command': 'create_delay_corner',  # Which command block
                    'extract_param': '-rc_corner',  # Which parameter to extract
                    'match_param': '-early_analysis_domain'  # Parameter to match search value
                }]
            initial_values: Starting values for first stage (e.g., domain names)
        
        Returns:
            Dict mapping initial values to final extracted values
        
        Example:
            # Extract QRC tech through domain → rc_corner → qrc_tech
            chain_spec = [
                {
                    'in_command': 'create_delay_corner',
                    'match_param': '-early_analysis_domain',
                    'extract_param': '-rc_corner'
                },
                {
                    'in_command': 'create_rc_corner',
                    'match_param': '-name',
                    'extract_param': '-qrc_tech'
                }
            ]
            result = self.extract_chain(log_files, chain_spec, initial_values=domains)
        """
        if not initial_values:
            return {}
        
        results = {}
        
        for initial_value in initial_values:
            current_value = initial_value
            
            # Walk through chain stages
            for stage in chain_spec:
                next_value = None
                
                # Search in each log file
                for log_file in log_files:
                    # Extract command blocks
                    blocks = self.extract_command_blocks(
                        log_file,
                        command=stage['in_command'],
                        extract_params=[stage['match_param'], stage['extract_param']]
                    )
                    
                    # Find matching block
                    for block in blocks['blocks']:
                        if block['params'].get(stage['match_param']) == current_value:
                            next_value = block['params'].get(stage['extract_param'])
                            break
                    
                    if next_value:
                        break
                
                if not next_value:
                    break
                
                current_value = next_value
            
            if current_value != initial_value:
                results[initial_value] = current_value
        
        return results
    
    # =========================================================================
    # Pattern 7: Simple List Extraction (from IMP-6-0-0-02, IMP-13-0-0-00)
    # =========================================================================
    
    def extract_simple_list(
        self,
        log_file: Path,
        skip_patterns: Optional[List[str]] = None,
        line_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract simple list of items from log (one item per line).
        
        Use cases:
        - Black box module list
        - Command list (e.g., add_pin_constraints)
        
        Args:
            log_file: Path to log file
            skip_patterns: Patterns to skip (e.g., header lines, separators)
            line_filter: Only include lines matching this pattern
        
        Returns:
            Dict with structure:
            {
                'items': [item1, item2, ...],
                'metadata': {item: {line_number, file_path}}
            }
        
        Example:
            # Extract black box modules (skip headers)
            result = self.extract_simple_list(
                log_file,
                skip_patterns=[r'---', r'Module']
            )
        """
        if hasattr(self, 'read_file'):
            lines = self.read_file(log_file)
        else:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.read().splitlines()
        
        skip_patterns = skip_patterns or []
        skip_regexes = [re.compile(p, re.IGNORECASE) for p in skip_patterns]
        filter_regex = re.compile(line_filter, re.IGNORECASE) if line_filter else None
        
        items = []
        metadata = {}
        seen = set()
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
            
            # Skip patterns
            if any(regex.search(line_stripped) for regex in skip_regexes):
                continue
            
            # Apply filter if provided
            if filter_regex and not filter_regex.search(line_stripped):
                continue
            
            # Extract item
            item = line_stripped
            if item not in seen:
                seen.add(item)
                items.append(item)
                metadata[item] = {
                    'line_number': line_num,
                    'file_path': str(log_file),
                    'line_content': line_stripped
                }
        
        return {
            'items': items,
            'metadata': metadata,
            'count': len(items),
            'log_file': str(log_file)
        }
