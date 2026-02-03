################################################################################
# Script Name: IMP-10-0-0-00.py
#
# Purpose:
#   Confirm the netlist/spef version is correct.
#   Parse STA log to find netlist/SPEF files, then extract version information
#   from actual files.
#
# Logic:
#   - Parse sta_post_syn.log to extract netlist/SPEF file paths and status
#   - Read netlist file (.v/.v.gz) to get Genus version and generation date
#   - Read SPEF file (.spef/.spef.gz) to get Quantus version and generation date
#   - Verify files are loaded successfully
#   - "Skipping SPEF reading" counts as FAIL
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value>0 → Value with waiver logic
#   Type 4: requirements.value=N/A, waivers.value>0 → Boolean with waiver logic
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Template Usage:
#   - OutputBuilderMixin: Used for consistent output formatting (v1.1.0)
#   - Custom parsing: Specialized netlist/SPEF file parsing logic retained
#
# Refactored: 2025-12-11 (Partial template integration)
#
# Author: yyin
# Date: 2025-12-02
################################################################################

from pathlib import Path
import re
import sys
import gzip
from typing import List, Dict, Tuple, Optional, Any


# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # Go up to Check_modules/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker, CheckResult, ConfigurationError
from output_formatter import DetailItem, Severity, create_check_result
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin


class NetlistSpefVersionChecker(BaseChecker, WaiverHandlerMixin, OutputBuilderMixin):
    """
    Unified checker that auto-detects and handles all 4 checker types.
    Uses WaiverHandlerMixin for waiver=0 detection and OutputBuilderMixin for consistent output formatting.
    
    Check Target: Confirm the netlist/spef version is correct
    
    Type Detection Logic:
    - Type 1: requirements.value=N/A AND waivers.value=N/A/0
    - Type 2: requirements.value>0 AND pattern_items AND waivers.value=N/A/0
    - Type 3: requirements.value>0 AND pattern_items AND waivers.value>0
    - Type 4: requirements.value=N/A AND waivers.value>0
    """
    
    def __init__(self):
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-00",
            item_desc="Confirm the netlist/spef version is correct"
        )
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._netlist_info: Dict[str, Any] = {}
        self._spef_info: Dict[str, Any] = {}
        self._sta_log_info: Dict[str, Any] = {}
    
    def _read_file_content(self, file_path: Path, max_lines: int = 100) -> List[str]:
        """
        Read file content, supporting both plain text and gzip compressed files.
        
        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to read from start
            
        Returns:
            List of lines from the file
        """
        if not file_path.exists():
            return []
        
        try:
            # Check if file is actually gzipped by trying to read it
            if file_path.suffix == '.gz':
                try:
                    with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= max_lines:
                                break
                            lines.append(line)
                        return lines
                except (gzip.BadGzipFile, OSError):
                    # Not a real gzip file, fall through to read as plain text
                    pass
            
            # Read as plain text file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return lines
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}")
            return []
    
    def _parse_netlist_version(self, netlist_path: Path) -> Dict[str, str]:
        """
        Parse netlist file to extract version information.
        
        Expected format:
        // Generated by Cadence Genus(TM) Synthesis Solution 23.15-s099_1
        // Generated on: Nov 18 2025 15:58:15 IST (Nov 18 2025 10:28:15 UTC)
        
        Returns:
            Dict with keys: tool, version, date, time
        """
        version_info = {
            'tool': '',
            'version': '',
            'date': '',
            'time': '',
            'full_timestamp': ''
        }
        
        if not netlist_path.exists():
            return version_info
        
        lines = self._read_file_content(netlist_path, max_lines=50)
        
        for line in lines:
            # Extract tool and version: "Generated by Cadence Genus(TM) Synthesis Solution 23.15-s099_1"
            if 'Generated by' in line and 'Genus' in line:
                # Extract version number
                match = re.search(r'Synthesis Solution\s+([\d\.\-\w]+)', line)
                if match:
                    version_info['tool'] = 'Cadence Genus Synthesis Solution'
                    version_info['version'] = match.group(1)
            
            # Extract generation date: "Generated on: Nov 18 2025 15:58:15 IST"
            elif 'Generated on:' in line:
                # Extract date and time
                match = re.search(r'Generated on:\s+(\w+\s+\d+\s+\d+)\s+([\d:]+)', line)
                if match:
                    version_info['date'] = match.group(1)
                    version_info['time'] = match.group(2)
                    version_info['full_timestamp'] = f"{match.group(1)} {match.group(2)}"
        
        return version_info
    
    def _parse_spef_version(self, spef_path: Path) -> Dict[str, str]:
        """
        Parse SPEF file to extract version information.
        
        Expected format:
        *SPEF "IEEE 1481-1999"
        *DESIGN "cdn_sd2101_i3p765_vm130_6x2ya2yb2yc2yd1ye1ga1gb"
        *DATE "Tue Jun 10 14:16:48 2025"
        *VENDOR "Cadence Design Systems Inc"
        *PROGRAM "Cadence Quantus Extraction"
        *VERSION "23.1.0-p075 Tue Sep 26 09:27:40 PDT 2023"
        
        Returns:
            Dict with keys: design, date, vendor, program, version
        """
        version_info = {
            'design': '',
            'date': '',
            'vendor': '',
            'program': '',
            'version': '',
            'spef_standard': ''
        }
        
        if not spef_path.exists():
            return version_info
        
        lines = self._read_file_content(spef_path, max_lines=100)
        
        for line in lines:
            # *SPEF "IEEE 1481-1999"
            if line.startswith('*SPEF'):
                match = re.search(r'\*SPEF\s+"([^"]+)"', line)
                if match:
                    version_info['spef_standard'] = match.group(1)
            
            # *DESIGN "design_name"
            elif line.startswith('*DESIGN'):
                match = re.search(r'\*DESIGN\s+"([^"]+)"', line)
                if match:
                    version_info['design'] = match.group(1)
            
            # *DATE "Tue Jun 10 14:16:48 2025"
            elif line.startswith('*DATE'):
                match = re.search(r'\*DATE\s+"([^"]+)"', line)
                if match:
                    version_info['date'] = match.group(1)
            
            # *VENDOR "Cadence Design Systems Inc"
            elif line.startswith('*VENDOR'):
                match = re.search(r'\*VENDOR\s+"([^"]+)"', line)
                if match:
                    version_info['vendor'] = match.group(1)
            
            # *PROGRAM "Cadence Quantus Extraction"
            elif line.startswith('*PROGRAM'):
                match = re.search(r'\*PROGRAM\s+"([^"]+)"', line)
                if match:
                    version_info['program'] = match.group(1)
            
            # *VERSION "23.1.0-p075 Tue Sep 26 09:27:40 PDT 2023"
            elif line.startswith('*VERSION'):
                match = re.search(r'\*VERSION\s+"([^"]+)"', line)
                if match:
                    version_info['version'] = match.group(1)
        
        return version_info
    
    def _resolve_relative_path(self, relative_path: str, sta_log_dir: Path) -> Optional[Path]:
        """
        Resolve relative path from STA log to absolute path.
        
        Args:
            relative_path: Relative path from STA log (e.g., "../../data/syn_opt/...")
            sta_log_dir: Directory containing the STA log file
            
        Returns:
            Absolute path if exists, None otherwise
        """
        if not relative_path:
            return None
        
        # Try to resolve from STA log directory
        try:
            # Clean path
            clean_path = relative_path.strip().strip('"').strip("'")
            
            # Resolve relative to STA log directory
            abs_path = (sta_log_dir / clean_path).resolve()
            
            if abs_path.exists():
                return abs_path
            
            # If not found, try from project root
            if self.root:
                abs_path = (self.root / clean_path).resolve()
                if abs_path.exists():
                    return abs_path
        except Exception as e:
            print(f"Warning: Failed to resolve path {relative_path}: {e}")
        
        return None
    
    def _parse_sta_log(self) -> Dict[str, Any]:
        """
        Parse STA log file to extract netlist/SPEF information.
        
        Returns:
            Dict with keys:
            - netlist_path: Path to netlist file
            - netlist_status: Success/Failed
            - spef_path: Path to SPEF file (if any)
            - spef_status: Success/Failed/Skipped
            - errors: List of error messages
        """
        sta_info = {
            'netlist_path': None,
            'netlist_status': 'Not Found',
            'spef_path': None,
            'spef_status': 'Not Found',
            'errors': [],
            'warnings': []
        }
        
        # Validate input_files configuration
        if not self.item_data or 'input_files' not in self.item_data:
            raise ConfigurationError("No input_files specified in configuration")
        
        input_files = self.item_data['input_files']
        
        # Check if input_files is empty
        if not input_files:
            raise ConfigurationError("input_files is empty in configuration")
        
        if isinstance(input_files, str):
            input_files = [input_files]
        
        # Check if list is empty after conversion
        if not input_files:
            raise ConfigurationError("input_files list is empty")
        
        for file_path_str in input_files:
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                sta_info['errors'].append(f"STA log file not found: {file_path_str}")
                continue
            
            sta_log_dir = file_path.parent
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                # Extract netlist file path
                # <CMD> read_netlist ../../data/syn_opt/dbs/syn_opt.block_finish.cdb/cmn/phy_cmn_phase_align_digtop.v.gz
                if 'read_netlist' in line and '<CMD>' in line:
                    match = re.search(r'read_netlist\s+(\S+)', line)
                    if match:
                        netlist_rel_path = match.group(1)
                        netlist_abs_path = self._resolve_relative_path(netlist_rel_path, sta_log_dir)
                        # Store path even if file doesn't exist
                        if netlist_abs_path:
                            sta_info['netlist_path'] = netlist_abs_path
                        else:
                            # Store relative path info for reference
                            sta_info['netlist_relative_path'] = netlist_rel_path
                        
                        self._metadata['netlist_cmd'] = {
                            'line_number': line_num,
                            'file_path': str(file_path),
                            'relative_path': netlist_rel_path
                        }
                
                # Reading verilog netlist '...'
                elif 'Reading verilog netlist' in line:
                    match = re.search(r"Reading verilog netlist\s+'([^']+)'", line)
                    if match:
                        netlist_rel_path = match.group(1)
                        if not sta_info.get('netlist_path'):
                            netlist_abs_path = self._resolve_relative_path(netlist_rel_path, sta_log_dir)
                            if netlist_abs_path:
                                sta_info['netlist_path'] = netlist_abs_path
                            else:
                                sta_info['netlist_relative_path'] = netlist_rel_path
                    
                    self._metadata['netlist_reading'] = {
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }
                
                # Check netlist success: "*** Netlist is unique."
                elif '*** Netlist is unique' in line or 'Netlist is unique' in line:
                    sta_info['netlist_status'] = 'Success'
                    self._metadata['netlist_success'] = {
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }
                
                # Check for SPEF reading
                # [INFO] Skipping SPEF reading as we are writing post-synthesis SDF files
                elif 'Skipping SPEF reading' in line:
                    sta_info['spef_status'] = 'Skipped'
                    sta_info['errors'].append("SPEF reading was skipped")
                    self._metadata['spef_skipped'] = {
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'reason': line.strip()
                    }
                
                # read_parasitics step
                elif 'Begin flow_step read_parasitics' in line:
                    self._metadata['spef_step_begin'] = {
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }
                
                elif 'End flow_step read_parasitics' in line:
                    self._metadata['spef_step_end'] = {
                        'line_number': line_num,
                        'file_path': str(file_path)
                    }
                    # If SPEF was not skipped and step completed, assume success
                    if sta_info['spef_status'] != 'Skipped':
                        sta_info['spef_status'] = 'Success'
                
                # Look for SPEF file path
                # read_spef or similar command
                elif 'read_spef' in line.lower() or 'read_parasitics' in line.lower():
                    # Try to extract SPEF file path
                    match = re.search(r'([\w/\.\-]+\.spef(?:\.gz)?)', line, re.IGNORECASE)
                    if match:
                        spef_rel_path = match.group(1)
                        spef_abs_path = self._resolve_relative_path(spef_rel_path, sta_log_dir)
                        if spef_abs_path:
                            sta_info['spef_path'] = spef_abs_path
                
                # Check for errors
                elif re.search(r'\b(error|failed)\b', line, re.IGNORECASE):
                    if 'netlist' in line.lower() or 'spef' in line.lower():
                        sta_info['errors'].append(f"Line {line_num}: {line.strip()}")
        
        # Final status determination
        if sta_info.get('netlist_relative_path') or sta_info.get('netlist_path'):
            # Netlist command found
            if 'netlist_success' in self._metadata:
                sta_info['netlist_status'] = 'Success'
            elif sta_info['netlist_status'] == 'Not Found':
                # Command found but status unknown
                sta_info['netlist_status'] = 'Read Command Found'
        
        return sta_info
    
    def _parse_input_files(self) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        """
        Parse input files to extract netlist and SPEF version information.
        
        Returns:
            Tuple of (netlist_info, spef_info, error_list)
        """
        # Parse STA log first
        self._sta_log_info = self._parse_sta_log()
        
        netlist_info = {}
        spef_info = {}
        errors = list(self._sta_log_info.get('errors', []))
        
        # Parse netlist file if found
        if self._sta_log_info.get('netlist_path'):
            netlist_path = self._sta_log_info['netlist_path']
            netlist_info = self._parse_netlist_version(netlist_path)
            netlist_info['path'] = str(netlist_path)
            netlist_info['status'] = self._sta_log_info.get('netlist_status', 'Unknown')
            
            if not netlist_info.get('version'):
                errors.append(f"Failed to extract version from netlist: {netlist_path.name}")
        elif self._sta_log_info.get('netlist_relative_path'):
            # Netlist path found but file doesn't exist
            netlist_info['relative_path'] = self._sta_log_info['netlist_relative_path']
            netlist_info['status'] = self._sta_log_info.get('netlist_status', 'Unknown')
            netlist_info['note'] = 'File path found in log but actual file not accessible'
        else:
            errors.append("Netlist file path not found in STA log")
        
        # Parse SPEF file if found
        if self._sta_log_info.get('spef_path'):
            spef_path = self._sta_log_info['spef_path']
            spef_info = self._parse_spef_version(spef_path)
            spef_info['path'] = str(spef_path)
            spef_info['status'] = self._sta_log_info.get('spef_status', 'Unknown')
            
            if not spef_info.get('version'):
                errors.append(f"Failed to extract version from SPEF: {spef_path.name}")
        else:
            # SPEF might be intentionally skipped or not found
            spef_status = self._sta_log_info.get('spef_status', 'Not Found')
            spef_info['status'] = spef_status
            if spef_status == 'Skipped':
                # Get skip reason from metadata
                metadata = self._metadata.get('spef_skipped', {})
                skip_reason = metadata.get('reason', 'SPEF reading was skipped')
                # Remove [INFO] prefix if present
                skip_reason = skip_reason.replace('[INFO] ', '')
                spef_info['skip_reason'] = skip_reason
            elif spef_status == 'Not Found':
                if 'spef_step_end' not in self._metadata:
                    errors.append("SPEF file path not found in STA log")
        
        return netlist_info, spef_info, errors
    
    def _match_pattern(self, text: str, patterns: List[str]) -> Optional[str]:
        """
        Check if text matches any pattern.
        
        Args:
            text: Text to check
            patterns: List of patterns (supports wildcards)
            
        Returns:
            Matched pattern if found, None otherwise
        """
        for pattern in patterns:
            try:
                # Convert wildcard to regex
                regex_pattern = pattern
                if '*' in pattern and not pattern.startswith('^'):
                    regex_pattern = pattern.replace('*', '.*')
                
                if re.search(regex_pattern, text, re.IGNORECASE):
                    return pattern
            except re.error:
                # Regex error, try exact match
                if pattern.lower() in text.lower():
                    return pattern
        return None
    
    def _get_waive_items_with_reasons(self) -> Dict[str, str]:
        """
        Get waiver items with their reasons.
        
        Returns:
            Dict mapping waive_item to reason string
        """
        waivers = self.get_waivers()
        if not waivers:
            return {}
        
        waive_items = waivers.get('waive_items', [])
        
        # If it's a list of dicts with 'name' and 'reason'
        if waive_items and isinstance(waive_items[0], dict):
            return {item['name']: item.get('reason', '') for item in waive_items}
        
        # If it's a simple list
        return {item: '' for item in waive_items}
    
    def _execute_type1(self, netlist_info: Dict[str, Any], spef_info: Dict[str, Any], 
                       errors: List[str]) -> CheckResult:
        """
        Type 1: Boolean check with automatic waiver.value=0 support
        
        Check if netlist and SPEF are loaded successfully.
        "Skipping SPEF reading" counts as FAIL.
        
        Waiver Logic (Automatic via build_complete_output):
        - waiver.value = 0: Auto-convert FAIL→INFO, force PASS [WAIVED_AS_INFO]
                           Auto-parse waive_items and output as INFO [WAIVED_INFO]
        - waiver.value = N/A: Normal mode
        """
        found_items = {}
        missing_items = []
        
        # Check netlist
        netlist_status = netlist_info.get('status', 'Not Found')
        if netlist_status == 'Success':
            if netlist_info.get('path'):
                netlist_path = netlist_info.get('path', 'Unknown')
                version_str = netlist_info.get('version', 'Unknown')
                date_str = netlist_info.get('full_timestamp', netlist_info.get('date', 'Unknown'))
                
                metadata = self._metadata.get('netlist_success', {})
                item_name = f"Netlist: {netlist_path}"
                found_items[item_name] = {
                    'line_number': metadata.get('line_number', ''),
                    'file_path': metadata.get('file_path', ''),
                    'version': version_str,
                    'date': date_str
                }
            elif netlist_info.get('relative_path'):
                netlist_rel_path = netlist_info['relative_path']
                metadata = self._metadata.get('netlist_success', {})
                item_name = f"Netlist: {netlist_rel_path}"
                found_items[item_name] = {
                    'line_number': metadata.get('line_number', ''),
                    'file_path': metadata.get('file_path', ''),
                    'note': 'found in log, file not accessible'
                }
        else:
            missing_items.append(f"Netlist (Status: {netlist_status})")
        
        # Check SPEF
        spef_status = spef_info.get('status', 'Not Found')
        if spef_status == 'Success':
            if spef_info.get('path'):
                spef_path = spef_info.get('path', 'Unknown')
                version_str = spef_info.get('version', 'Unknown')
                date_str = spef_info.get('date', 'Unknown')
                
                metadata = self._metadata.get('spef_step_end', {})
                item_name = f"SPEF: {spef_path}"
                found_items[item_name] = {
                    'line_number': metadata.get('line_number', ''),
                    'file_path': metadata.get('file_path', ''),
                    'version': version_str,
                    'date': date_str
                }
        elif spef_status == 'Skipped':
            metadata = self._metadata.get('spef_skipped', {})
            skip_reason = metadata.get('reason', 'SPEF reading was skipped')
            skip_reason = skip_reason.replace('[INFO] ', '')
            missing_items.append(f"SPEF Reading was skipped ({skip_reason})")
        else:
            missing_items.append(f"SPEF (Status: {spef_status})")
        
        # Add other errors
        for error in errors:
            if not any(e in error for e in ["SPEF reading was skipped"]):
                missing_items.append(f"Error: {error}")
        
        # Name extractor to format output
        def extract_name(name, metadata):
            if isinstance(metadata, dict):
                version = metadata.get('version', '')
                date = metadata.get('date', '')
                note = metadata.get('note', '')
                if version and date:
                    return f"{name}, Version: {version}, Date: {date}"
                elif note:
                    return f"{name} ({note})"
            return name
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            value="N/A",
            has_pattern_items=False,
            has_waiver_value=False,
            default_file='N/A',
            name_extractor=extract_name,
            found_reason="Status: Success",
            missing_reason="File loading failed",
            found_desc="Netlist/SPEF files loaded successfully",
            missing_desc="Netlist/SPEF loading issues"
        )
    
    def _execute_type2(self, netlist_info: Dict[str, Any], spef_info: Dict[str, Any], 
                       errors: List[str]) -> CheckResult:
        """
        Type 2: Value comparison with automatic waiver.value=0 support
        
        Match required items in pattern_items against netlist/SPEF content.
        Expected value = number of items that should be found (should match pattern_items count).
        
        Waiver Logic (Automatic via build_complete_output):
        - waiver.value = 0: Auto-convert FAIL/WARN→INFO, force PASS [WAIVED_AS_INFO]
                           Auto-parse waive_items and output as INFO [WAIVED_INFO]
        - waiver.value = N/A: Normal mode
        """
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        found_items = {}
        missing_items = []
        extra_items = {}  # Items not in pattern (SPEF issues, etc.)
        
        # Collect all content to search
        all_content = []
        
        # Add netlist version info
        if netlist_info.get('tool'):
            all_content.append(f"Tool: {netlist_info['tool']}")
        if netlist_info.get('version'):
            all_content.append(f"Genus Synthesis Solution {netlist_info['version']}")
        if netlist_info.get('full_timestamp'):
            all_content.append(f"Generated on: {netlist_info['full_timestamp']}")
        
        # Add SPEF version info
        if spef_info.get('program'):
            all_content.append(f"Program: {spef_info['program']}")
        if spef_info.get('version'):
            all_content.append(f"VERSION {spef_info['version']}")
        if spef_info.get('date'):
            all_content.append(f"DATE {spef_info['date']}")
        
        # Match patterns against content
        matched_patterns = set()
        for pattern in pattern_items:
            found = False
            matched_content = None
            for content in all_content:
                if self._match_pattern(content, [pattern]):
                    found = True
                    matched_content = content
                    break
            
            if found:
                matched_patterns.add(pattern)
                # Build found_items with file/version metadata
                if netlist_info.get('path') and ('Genus' in pattern or 'Generated on' in pattern):
                    metadata = self._metadata.get('netlist_success', {})
                    found_items[pattern] = {
                        'line_number': metadata.get('line_number', ''),
                        'file_path': metadata.get('file_path', ''),
                        'matched': matched_content
                    }
                elif spef_info.get('path') and ('Quantus' in pattern or 'DATE' in pattern or 'VERSION' in pattern):
                    metadata = self._metadata.get('spef_step_end', {})
                    found_items[pattern] = {
                        'line_number': metadata.get('line_number', ''),
                        'file_path': metadata.get('file_path', ''),
                        'matched': matched_content
                    }
                else:
                    found_items[pattern] = {
                        'line_number': '',
                        'file_path': '',
                        'matched': matched_content
                    }
        
        # Find unmatched patterns
        missing_items = [p for p in pattern_items if p not in matched_patterns]
        
        # Check SPEF skip status - add as extra_item if skipped
        if spef_info.get('status') == 'Skipped':
            metadata = self._metadata.get('spef_skipped', {})
            skip_reason = spef_info.get('skip_reason', 'SPEF reading was skipped')
            extra_items["SPEF Reading was skipped"] = {
                'line_number': metadata.get('line_number', ''),
                'file_path': metadata.get('file_path', ''),
                'reason': skip_reason
            }
        
        # Add other errors as extra items
        for error in errors:
            if not any(e in error for e in ["SPEF reading was skipped"]):
                extra_items[f"Error: {error}"] = {
                    'line_number': '',
                    'file_path': '',
                    'reason': 'Unexpected error'
                }
        
        # Name extractor
        def extract_name(name, metadata):
            if isinstance(metadata, dict):
                matched = metadata.get('matched', '')
                reason = metadata.get('reason', '')
                if matched:
                    return f"{name}: {matched}"
                elif reason:
                    return f"{name}: {reason}"
            return name
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            extra_items=extra_items,
            value=len(found_items),
            has_pattern_items=True,
            has_waiver_value=False,
            default_file='N/A',
            name_extractor=extract_name,
            found_reason="Version pattern matched",
            missing_reason="Required pattern not found",
            extra_reason="Design has no spef/netlist file or unexpected error",
            found_desc="Netlist/SPEF version is correct",
            missing_desc="Netlist/SPEF version isn't correct",
            extra_desc="Design has no spef/netlist file"
        )
    
    def _execute_type3(self, netlist_info: Dict[str, Any], spef_info: Dict[str, Any], 
                       errors: List[str]) -> CheckResult:
        """
        Type 3: Value comparison with waiver logic
        
        Match required items in pattern_items, allow waiving missing items.
        Expected value = number of items that should be found (excluding waived items).
        """
        requirements = self.get_requirements()
        expected_value = requirements.get('value', 0) if requirements else 0
        try:
            expected_value = int(expected_value)
        except:
            expected_value = 0
        
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        details = []
        matched_items = []
        
        # Collect all content to search
        all_content = []
        
        # Add netlist version info
        if netlist_info.get('tool'):
            all_content.append(f"Tool: {netlist_info['tool']}")
        if netlist_info.get('version'):
            all_content.append(f"Genus Synthesis Solution {netlist_info['version']}")
        if netlist_info.get('full_timestamp'):
            all_content.append(f"Generated on: {netlist_info['full_timestamp']}")
        
        # Add SPEF version info
        if spef_info.get('program'):
            all_content.append(f"Program: {spef_info['program']}")
        if spef_info.get('version'):
            all_content.append(f"VERSION {spef_info['version']}")
        if spef_info.get('date'):
            all_content.append(f"DATE {spef_info['date']}")
        
        # Match patterns against content
        for pattern in pattern_items:
            found = False
            matched_content = None
            for content in all_content:
                if self._match_pattern(content, [pattern]):
                    found = True
                    matched_content = content
                    break
            
            if found:
                matched_items.append((pattern, matched_content))
        
        # Find unmatched patterns (missing required items)
        matched_patterns = set(pattern for pattern, _ in matched_items)
        unmatched_patterns = [p for p in pattern_items if p not in matched_patterns]
        
        # Classify unmatched as waived/unwaived
        unwaived_missing = []
        waived_missing = []
        
        for pattern in unmatched_patterns:
            # Check if pattern matches any waiver (partial match allowed)
            is_waived = False
            matched_waiver = None
            for waiver_key in waive_items:
                if waiver_key.lower() in pattern.lower() or pattern.lower() in waiver_key.lower():
                    is_waived = True
                    matched_waiver = waiver_key
                    break
            
            if is_waived:
                waived_missing.append((pattern, matched_waiver))
            else:
                unwaived_missing.append(pattern)
        
        # Find unused waivers
        used_waivers = set(w for _, w in waived_missing)
        unused_waivers = [w for w in waive_items if w not in used_waivers]
        
        # Track errors for different groups
        version_error_details = []
        spef_skip_details = []
        waiver_warn_details = []
        
        # Categorize unmatched patterns by type (similar to Type2)
        tool_patterns = []
        date_patterns = []
        
        for pattern in unwaived_missing:
            if 'Genus' in pattern or 'Synthesis' in pattern or 'Quantus' in pattern or 'Extraction' in pattern:
                tool_patterns.append(pattern)
            elif 'Generated on' in pattern or '202' in pattern or 'DATE' in pattern:
                date_patterns.append(pattern)
            else:
                # Generic pattern
                version_error_details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Required pattern not found"
                ))
        
        # Generate combined error message if there are tool/date patterns
        if tool_patterns or date_patterns:
            if tool_patterns and date_patterns:
                error_msg = f"The required netlist's version is generated on {date_patterns[0]} using {tool_patterns[0]}"
            elif date_patterns:
                error_msg = f"The required netlist's version is generated on {date_patterns[0]}"
            else:
                error_msg = f"The required netlist's version is generated by {tool_patterns[0]}"
            
            version_error_details.append(DetailItem(
                severity=Severity.FAIL,
                name=error_msg,
                line_number='',
                file_path='',
                reason="Version mismatch"
            ))
        
        # Add version errors to details
        details.extend(version_error_details)
        
        # Check if SPEF is skipped and if it can be waived
        spef_skipped = (spef_info.get('status') == 'Skipped')
        spef_skip_waived = False
        
        if spef_skipped:
            # Check if SPEF skip can be waived
            spef_skip_text = "SPEF Reading was skipped"
            for waiver_key in waive_items:
                # Check for word-level match (all words in waiver must appear in text)
                waiver_words = set(waiver_key.lower().split())
                text_words = set(spef_skip_text.lower().split())
                if waiver_words.issubset(text_words) or waiver_key.lower() in spef_skip_text.lower() or spef_skip_text.lower() in waiver_key.lower():
                    spef_skip_waived = True
                    # Remove from unused_waivers if it's there
                    if waiver_key in unused_waivers:
                        unused_waivers.remove(waiver_key)
                    break
        
        is_pass = (len(unwaived_missing) == 0) and (not spef_skipped or spef_skip_waived)
        
        # Build matched patterns summary for reason
        version_matched = (len(matched_items) == expected_value)
        
        if version_matched:
            matched_patterns_summary = ', '.join([f"'{pattern}'" for pattern, _ in matched_items])
            version_check_reason = f"Matched {len(matched_items)}/{expected_value} required patterns: {matched_patterns_summary}"
        else:
            version_check_reason = f"Version check failed: Matched {len(matched_items)}/{expected_value} required patterns"
        
        # INFO items for waived missing patterns
        waived_info_details = []
        for pattern, waiver_key in waived_missing:
            waiver_reason = waive_items_dict.get(waiver_key, '')
            reason = f"{waiver_reason}[WAIVER]" if waiver_reason else f"Waived missing item[WAIVER]"
            waived_info_details.append(DetailItem(
                severity=Severity.INFO,
                name=pattern,
                line_number='',
                file_path='',
                reason=reason
            ))
        details.extend(waived_info_details)
        
        # WARN: Unused waivers
        for waiver in unused_waivers:
            waiver_warn_details.append(DetailItem(
                severity=Severity.WARN,
                name=waiver,
                line_number='',
                file_path='',
                reason="Waived item not used[WAIVER]"
            ))
        details.extend(waiver_warn_details)
        
        # INFO items - detailed file info
        info_details = []
        
        if netlist_info.get('status') == 'Success' and netlist_info.get('path'):
            netlist_path = netlist_info.get('path', 'Unknown')
            version_str = netlist_info.get('version', 'Unknown')
            date_str = netlist_info.get('full_timestamp', netlist_info.get('date', 'Unknown'))
            metadata = self._metadata.get('netlist_success', {})
            info_details.append(DetailItem(
                severity=Severity.INFO,
                name=f"Netlist path: {netlist_path}, Version: {version_str}, Date: {date_str}",
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=version_check_reason
            ))
        elif netlist_info.get('relative_path'):
            netlist_rel_path = netlist_info['relative_path']
            metadata = self._metadata.get('netlist_success', {})
            info_details.append(DetailItem(
                severity=Severity.INFO,
                name=f"Netlist path: {netlist_rel_path}",
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Status: Success (found in log, file not accessible for version check)"
            ))
        
        if spef_info.get('status') == 'Success' and spef_info.get('path'):
            spef_path = spef_info.get('path', 'Unknown')
            version_str = spef_info.get('version', 'Unknown')
            date_str = spef_info.get('date', 'Unknown')
            metadata = self._metadata.get('spef_step_end', {})
            info_details.append(DetailItem(
                severity=Severity.INFO,
                name=f"SPEF path: {spef_path}, Version: {version_str}, Date: {date_str}",
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Status: Success"
            ))
        elif spef_info.get('status') == 'Skipped':
            skip_reason = spef_info.get('skip_reason', 'SPEF reading was skipped')
            metadata = self._metadata.get('spef_skipped', {})
            
            # Check if SPEF skip is waived (Type3 specific)
            if spef_skip_waived:
                # Find matching waiver and get reason
                matched_waiver_key = None
                spef_skip_text = "SPEF Reading was skipped"
                for waiver_key in waive_items:
                    # Check for word-level match (all words in waiver must appear in text)
                    waiver_words = set(waiver_key.lower().split())
                    text_words = set(spef_skip_text.lower().split())
                    if waiver_words.issubset(text_words) or waiver_key.lower() in spef_skip_text.lower() or spef_skip_text.lower() in waiver_key.lower():
                        matched_waiver_key = waiver_key
                        break
                
                waiver_reason = waive_items_dict.get(matched_waiver_key, '') if matched_waiver_key else ''
                spef_skip_detail = DetailItem(
                    severity=Severity.INFO,
                    name=f"SPEF Reading was skipped",
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"{waiver_reason}[WAIVER]" if waiver_reason else f"{skip_reason}[WAIVER]"
                )
                info_details.append(spef_skip_detail)
            else:
                # Add as FAIL
                spef_skip_detail = DetailItem(
                    severity=Severity.FAIL,
                    name=f"SPEF Reading was skipped",
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=skip_reason
                )
                spef_skip_details = [spef_skip_detail]
                details.append(spef_skip_detail)
        
        details.extend(info_details)
        
        # Build groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        # ERROR01: Design has no spef/netlist file
        if spef_skip_details:
            error_groups["ERROR01"] = {
                "description": "Design has no spef/netlist file",
                "items": [d.name for d in spef_skip_details]
            }
        
        # ERROR02: Netlist/spef version isn't correct
        if version_error_details:
            error_groups["ERROR02"] = {
                "description": "Netlist/spef version isn't correct",
                "items": [d.name for d in version_error_details]
            }
        
        # WARN01: Unused waivers
        if waiver_warn_details:
            warn_groups["WARN01"] = {
                "description": "Unused waivers",
                "items": [d.name for d in waiver_warn_details]
            }
        
        # INFO01: Netlist/spef version is correct (if version matched)
        all_info_items = info_details + waived_info_details
        if all_info_items:
            if version_matched:
                info_groups["INFO01"] = {
                    "description": "Netlist/spef version is correct",
                    "items": [d.name for d in all_info_items]
                }
            else:
                info_groups["INFO01"] = {
                    "description": "Netlist/SPEF version check",
                    "items": [d.name for d in all_info_items]
                }
        
        return create_check_result(
            value=len(matched_items),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
        

    def _execute_type4(self, netlist_info: Dict[str, Any], spef_info: Dict[str, Any], 
                       errors: List[str]) -> CheckResult:
        """
        Type 4: Boolean check with waiver logic
        
        Check if netlist/SPEF are loaded successfully.
        Expected value = "yes" (pass) or "no" (fail).
        """
        waive_items_dict = self._get_waive_items_with_reasons()
        waive_items = list(waive_items_dict.keys())
        
        details = []
        
        # Track details for different groups
        spef_skip_details = []
        waiver_warn_details = []
        
        # Check if SPEF is skipped and if it can be waived
        spef_skipped = (spef_info.get('status') == 'Skipped')
        spef_skip_waived = False
        
        if spef_skipped:
            # Check if SPEF skip can be waived
            spef_skip_text = "SPEF Reading was skipped"
            for waiver_key in waive_items:
                # Check for word-level match (all words in waiver must appear in text)
                waiver_words = set(waiver_key.lower().split())
                text_words = set(spef_skip_text.lower().split())
                if waiver_words.issubset(text_words) or waiver_key.lower() in spef_skip_text.lower() or spef_skip_text.lower() in waiver_key.lower():
                    spef_skip_waived = True
                    break
        
        is_pass = not spef_skipped or spef_skip_waived
        
        # INFO items - detailed file info
        info_details = []
        
        if netlist_info.get('status') == 'Success' and netlist_info.get('path'):
            netlist_path = netlist_info.get('path', 'Unknown')
            version_str = netlist_info.get('version', 'Unknown')
            date_str = netlist_info.get('full_timestamp', netlist_info.get('date', 'Unknown'))
            metadata = self._metadata.get('netlist_success', {})
            info_details.append(DetailItem(
                severity=Severity.INFO,
                name=f"Netlist path: {netlist_path}, Version: {version_str}, Date: {date_str}",
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Status: Success"
            ))
        elif netlist_info.get('relative_path'):
            netlist_rel_path = netlist_info['relative_path']
            metadata = self._metadata.get('netlist_success', {})
            info_details.append(DetailItem(
                severity=Severity.INFO,
                name=f"Netlist path: {netlist_rel_path}",
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Status: Success (found in log, file not accessible)"
            ))
        
        if spef_info.get('status') == 'Success' and spef_info.get('path'):
            spef_path = spef_info.get('path', 'Unknown')
            version_str = spef_info.get('version', 'Unknown')
            date_str = spef_info.get('date', 'Unknown')
            metadata = self._metadata.get('spef_step_end', {})
            info_details.append(DetailItem(
                severity=Severity.INFO,
                name=f"SPEF path: {spef_path}, Version: {version_str}, Date: {date_str}",
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason=f"Status: Success"
            ))
        elif spef_info.get('status') == 'Skipped':
            skip_reason = spef_info.get('skip_reason', 'SPEF reading was skipped')
            metadata = self._metadata.get('spef_skipped', {})
            
            # Check if SPEF skip is waived (Type4 specific)
            if spef_skip_waived:
                # Find matching waiver and get reason
                matched_waiver_key = None
                spef_skip_text = "SPEF Reading was skipped"
                for waiver_key in waive_items:
                    # Check for word-level match (all words in waiver must appear in text)
                    waiver_words = set(waiver_key.lower().split())
                    text_words = set(spef_skip_text.lower().split())
                    if waiver_words.issubset(text_words) or waiver_key.lower() in spef_skip_text.lower() or spef_skip_text.lower() in waiver_key.lower():
                        matched_waiver_key = waiver_key
                        break
                
                waiver_reason = waive_items_dict.get(matched_waiver_key, '') if matched_waiver_key else ''
                spef_skip_detail = DetailItem(
                    severity=Severity.INFO,
                    name=f"SPEF Reading was skipped",
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"{waiver_reason}[WAIVER]" if waiver_reason else f"{skip_reason}[WAIVER]"
                )
                info_details.append(spef_skip_detail)
            else:
                # Add as FAIL
                spef_skip_detail = DetailItem(
                    severity=Severity.FAIL,
                    name=f"SPEF Reading was skipped",
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=skip_reason
                )
                spef_skip_details = [spef_skip_detail]
                details.append(spef_skip_detail)
        
        details.extend(info_details)
        
        # Build groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        # ERROR01: Design has no spef/netlist file
        if spef_skip_details:
            error_groups["ERROR01"] = {
                "description": "Design has no spef/netlist file",
                "items": [d.name for d in spef_skip_details]
            }
        
        # INFO01: File information
        if info_details:
            if is_pass:
                info_groups["INFO01"] = {
                    "description": "Netlist/SPEF files loaded successfully",
                    "items": [d.name for d in info_details]
                }
            else:
                info_groups["INFO01"] = {
                    "description": "Netlist/SPEF file status",
                    "items": [d.name for d in info_details]
                }
        
        return create_check_result(
            value='yes' if is_pass else 'no',
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups if error_groups else None,
            warn_groups=warn_groups if warn_groups else None,
            info_groups=info_groups if info_groups else None,
            item_desc=self.item_desc
        )
    
    def execute_check(self) -> CheckResult:
        """
        Execute the check by auto-detecting type and calling appropriate method.
        
        Returns:
            CheckResult object containing check results
        """
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Parse input files
        netlist_info, spef_info, errors = self._parse_input_files()
        
        # Store for reference
        self._netlist_info = netlist_info
        self._spef_info = spef_info
        
        # Detect checker type
        checker_type = self.detect_checker_type()
        
        # Execute appropriate check based on type
        if checker_type == 1:
            return self._execute_type1(netlist_info, spef_info, errors)
        elif checker_type == 2:
            return self._execute_type2(netlist_info, spef_info, errors)
        elif checker_type == 3:
            return self._execute_type3(netlist_info, spef_info, errors)
        else:  # Type 4
            return self._execute_type4(netlist_info, spef_info, errors)


if __name__ == '__main__':
    checker = NetlistSpefVersionChecker()
    checker.run()
