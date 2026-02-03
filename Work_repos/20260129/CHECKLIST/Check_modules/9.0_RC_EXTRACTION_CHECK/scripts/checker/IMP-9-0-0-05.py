################################################################################
# Script Name: IMP-9-0-0-05.py
#
# Purpose:
#   Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)
#
# Logic:
#   - Parse input files: *.spef.gz (compressed SPEF files)
#   - Decompress .gz files and extract header section (first ~50 lines until *D_NET or *R_NET)
#   - Extract Quantus version from *VERSION line (format: major.minor.patch-build)
#   - Identify foundry/technology from TECH_VERSION (*DESIGN_FLOW) or TECH_FILE comment
#   - Map foundry identifier to minimum required Quantus version from configuration
#   - Compare extracted version against required version using numeric comparison
#   - Classify results: PASS if version >= required, FAIL if version < required or info missing
#   - Report per-file results with file path, found version, required version, and foundry
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Output Behavior (Type 2/3 - Check README "Output Behavior" section!):
#   status_check: pattern_items = items to CHECK STATUS (only output matched items)
#     - found_items = patterns matched AND version correct
#     - missing_items = patterns matched BUT version wrong
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2025-12-25 (Using checker_templates v1.1.0)
#
# Author: yyin
# Date: 2025-12-18
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

# MANDATORY: Import template mixins (checker_templates v1.1.0)
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin
from checker_templates.input_file_parser_template import InputFileParserMixin


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_9_0_0_05(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-9-0-0-05: Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # DESCRIPTION & REASON CONSTANTS - COPY FROM README Output Descriptions!
    # =========================================================================
    # Type 1/4: Boolean checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE1_4 = "SPEF files extracted with correct Quantus version"
    MISSING_DESC_TYPE1_4 = "SPEF files extracted with incorrect or missing Quantus version"
    FOUND_REASON_TYPE1_4 = "Quantus version meets foundry requirements"
    MISSING_REASON_TYPE1_4 = "Quantus version does not meet foundry requirements or version info missing"
    
    # Type 2/3: Pattern checks - COPY EXACT VALUES FROM README!
    FOUND_DESC_TYPE2_3 = "SPEF files with Quantus version matching or exceeding foundry requirements"
    MISSING_DESC_TYPE2_3 = "SPEF files with Quantus version below foundry requirements"
    FOUND_REASON_TYPE2_3 = "Quantus version {found_version} >= required {required_version} for {foundry}"
    MISSING_REASON_TYPE2_3 = "Quantus version {found_version} < required {required_version} for {foundry}"
    
    # All Types (waiver description) - COPY EXACT VALUES FROM README!
    WAIVED_DESC = "SPEF files with version violations waived by configuration"
    
    # Waiver parameters (Type 3/4 ONLY) - COPY EXACT VALUES FROM README!
    WAIVED_BASE_REASON = "Quantus version violation waived"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="9.0_RC_EXTRACTION_CHECK",
            item_id="IMP-9-0-0-05",
            item_desc="Confirm proper Quantus version is used for RC extraction(match to or mature than Foundry recommended Quantus version)"
        )
        self._parsed_spef_data: List[Dict[str, Any]] = []
        self._version_violations: List[Dict[str, Any]] = []
    
    # =========================================================================
    # Main Check Execution
    # =========================================================================
    
    def execute_check(self) -> CheckResult:
        """
        Execute check with automatic type detection and delegation.
        
        Returns:
            CheckResult based on detected checker type
        """
        try:
            if self.root is None:
                raise RuntimeError("Checker not initialized. Call init_checker() first.")
            
            # Detect checker type (use BaseChecker method)
            checker_type = self.detect_checker_type()
            
            # Execute based on type
            if checker_type == 1:
                return self._execute_type1()
            elif checker_type == 2:
                return self._execute_type2()
            elif checker_type == 3:
                return self._execute_type3()
            else:  # checker_type == 4
                return self._execute_type4()
        except ConfigurationError as e:
            return e.check_result
    
    # =========================================================================
    # Input Parsing (Common for All Types)
    # =========================================================================
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse SPEF files to extract Quantus version and foundry information.
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - SPEF file analysis results with metadata
            - 'metadata': Dict - Summary metadata
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files - IMPORTANT: returns tuple (valid_files_list, missing_files_list)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: LOGIC-001 - Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid SPEF files found")
        
        # 2. Parse SPEF files
        items = []
        errors = []
        
        for file_path in valid_files:
            try:
                spef_data = self._parse_spef_file(file_path)
                if spef_data:
                    items.append(spef_data)
                else:
                    errors.append(f"Failed to parse {file_path}")
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 3. Store on self
        self._parsed_spef_data = items
        
        # 4. Return aggregated dict
        return {
            'items': items,
            'metadata': {
                'total_files': len(valid_files),
                'parsed_files': len(items),
                'errors': len(errors)
            },
            'errors': errors
        }
    
    def _parse_spef_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single SPEF file to extract version and foundry information.
        
        Args:
            file_path: Path to SPEF file (.spef or .spef.gz)
            
        Returns:
            Dict with extracted data or None if parsing fails
        """
        # FIXED: SYNTAX-002 - Use Path().name to extract filename safely
        version_info = {
            'file_path': str(file_path),
            'file_name': Path(file_path).name,
            'quantus_version': None,
            'foundry': None,
            'tech_version': None,
            'design_name': None,
            'extraction_date': None,
            'line_number': 0
        }
        
        # Open file (handle .gz compression)
        # FIXED: Handle fake .gz files (not actually gzipped)
        f = None
        try:
            if str(file_path).endswith('.gz'):
                # Try gzip first
                try:
                    f = gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
                    # Test if it's really gzipped by reading one line
                    _ = f.readline()
                    f.seek(0)  # Reset to beginning
                except (gzip.BadGzipFile, OSError):
                    # Not a real gzip file, try plain text
                    f = open(file_path, 'r', encoding='utf-8', errors='ignore')
            else:
                f = open(file_path, 'r', encoding='utf-8', errors='ignore')
        except Exception as e:
            return None
        
        try:
            # Parse header section (first ~50 lines until *D_NET or *R_NET)
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Stop at net definitions
                if line.startswith('*D_NET') or line.startswith('*R_NET'):
                    break
                
                # Pattern 1: Extract Quantus version from VERSION header
                # Example: "*VERSION "22.1.1-s233 Mon Dec 11 23:26:00 PST 2023""
                if line.startswith('*VERSION'):
                    match = re.search(r'^\*VERSION\s+"([0-9]+\.[0-9]+\.[0-9]+(?:-s[0-9]+)?)\s+(.+)"$', line)
                    if match:
                        version_info['quantus_version'] = match.group(1)
                        version_info['line_number'] = line_num
                
                # Pattern 2: Extract extraction date
                # Example: "*DATE "Wed Nov 26 17:35:31 2025""
                elif line.startswith('*DATE'):
                    match = re.search(r'^\*DATE\s+"(.+)"$', line)
                    if match:
                        version_info['extraction_date'] = match.group(1)
                
                # Pattern 3: Extract technology version from DESIGN_FLOW
                # Example: "*DESIGN_FLOW "ROUTING_CONFIDENCE 100" "PIN_CAP NONE" "TECH_VERSION cln6_1p15m_1x1xa1ya5y2yy2yx2r_mim_ut-alrdl_rcbest_CCbest""
                elif '*DESIGN_FLOW' in line:
                    match = re.search(r'\*DESIGN_FLOW.*"TECH_VERSION\s+([^"]+)"', line)
                    if match:
                        version_info['tech_version'] = match.group(1)
                        # Extract foundry from tech version
                        foundry = self._identify_foundry_from_tech(match.group(1))
                        if foundry:
                            version_info['foundry'] = foundry
                
                # Pattern 4: Extract technology file path for foundry identification
                # Example: "// TECH_FILE /process/tsmcN6/data/g/QRC/15M1X1Xa1Ya5Y2Yy2Yx2R_UT/fs_v1d0p1a/rcbest/Tech/rcbest_CCbest/qrcTechFile"
                elif line.startswith('// TECH_FILE'):
                    match = re.search(r'^//\s*TECH_FILE\s+(.+)$', line)
                    if match:
                        tech_file = match.group(1)
                        foundry = self._identify_foundry_from_path(tech_file)
                        if foundry:
                            version_info['foundry'] = foundry
                
                # Pattern 5: Extract design name
                # Example: "*DESIGN "CDN_104H_cdn_hs_phy_data_slice_EW""
                elif line.startswith('*DESIGN'):
                    match = re.search(r'^\*DESIGN\s+"(.+)"$', line)
                    if match:
                        version_info['design_name'] = match.group(1)
        
        finally:
            f.close()
        
        return version_info
    
    def _identify_foundry_from_tech(self, tech_version: str) -> Optional[str]:
        """
        Identify foundry from TECH_VERSION string.
        
        Args:
            tech_version: Technology version string
            
        Returns:
            Foundry identifier or None
        """
        tech_lower = tech_version.lower()
        
        # TSMC patterns
        if 'cln6' in tech_lower or 'n6' in tech_lower:
            return 'TSMC_N6'
        elif 'cln5' in tech_lower or 'n5' in tech_lower:
            return 'TSMC_N5'
        elif 'cln4' in tech_lower or 'n4' in tech_lower:
            return 'TSMC_N4'
        elif 'cln3' in tech_lower or 'n3' in tech_lower:
            return 'TSMC_N3'
        
        # Samsung patterns
        elif '4lpp' in tech_lower:
            return 'SAMSUNG_4LPP'
        elif '5lpe' in tech_lower:
            return 'SAMSUNG_5LPE'
        
        # Intel patterns
        elif 'intel4' in tech_lower or 'intel_4' in tech_lower:
            return 'INTEL_4'
        
        # GlobalFoundries patterns
        elif '12lp' in tech_lower:
            return 'GF_12LP'
        
        return None
    
    def _identify_foundry_from_path(self, tech_file: str) -> Optional[str]:
        """
        Identify foundry from TECH_FILE path.
        
        Args:
            tech_file: Technology file path
            
        Returns:
            Foundry identifier or None
        """
        path_lower = tech_file.lower()
        
        # TSMC patterns
        if 'tsmcn6' in path_lower or 'tsmc/n6' in path_lower:
            return 'TSMC_N6'
        elif 'tsmcn5' in path_lower or 'tsmc/n5' in path_lower:
            return 'TSMC_N5'
        elif 'tsmcn4' in path_lower or 'tsmc/n4' in path_lower:
            return 'TSMC_N4'
        elif 'tsmcn3' in path_lower or 'tsmc/n3' in path_lower:
            return 'TSMC_N3'
        
        # Samsung patterns
        elif 'samsung' in path_lower and '4lpp' in path_lower:
            return 'SAMSUNG_4LPP'
        elif 'samsung' in path_lower and '5lpe' in path_lower:
            return 'SAMSUNG_5LPE'
        
        # Intel patterns
        elif 'intel' in path_lower and ('intel4' in path_lower or 'intel_4' in path_lower):
            return 'INTEL_4'
        
        # GlobalFoundries patterns
        elif ('globalfoundries' in path_lower or 'gf' in path_lower) and '12lp' in path_lower:
            return 'GF_12LP'
        
        return None
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two Quantus version strings.
        
        Args:
            version1: First version (e.g., "22.1.1-s233")
            version2: Second version (e.g., "22.1.0")
            
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """
        # Parse version components
        def parse_version(v: str) -> Tuple[int, int, int, int]:
            # Remove build suffix if present
            base_version = v.split('-')[0]
            # NOTE: split('.') is SAFE here - parsing VERSION STRING, not filename!
            # Example: "22.1.1-s233" -> ["22", "1", "1"]
            version_parts = base_version.split('.')
            major = int(version_parts[0]) if len(version_parts) > 0 else 0
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2]) if len(version_parts) > 2 else 0
            
            # Extract build number if present
            build = 0
            if '-s' in v:
                build_str = v.split('-s')[1]
                build = int(build_str) if build_str.isdigit() else 0
            
            return (major, minor, patch, build)
        
        v1_tuple = parse_version(version1)
        v2_tuple = parse_version(version2)
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Check if all SPEF files have correct Quantus version.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Check each SPEF file
        found_items = {}
        missing_items = []
        
        for spef_data in items:
            file_name = spef_data['file_name']
            quantus_version = spef_data.get('quantus_version')
            foundry = spef_data.get('foundry')
            
            # Type 1: Boolean check - verify version info exists
            if not quantus_version:
                missing_items.append(f"{file_name}: Missing Quantus version")
                continue
            
            if not foundry:
                missing_items.append(f"{file_name}: Cannot identify foundry")
                continue
            
            # Version info found - add to found_items
            found_items[file_name] = {
                'name': file_name,
                'line_number': spef_data.get('line_number', 0),
                'file_path': spef_data.get('file_path', 'N/A'),
                'reason': f"Quantus version {quantus_version}: {file_name} (Foundry: {foundry})",
                'version': quantus_version,
                'foundry': foundry
            }
        
        # README Display Format: Check if all files use same version and foundry
        if found_items:
            versions = set(m.get('version') for m in found_items.values())
            foundries = set(m.get('foundry') for m in found_items.values())
            
            if len(versions) == 1 and len(foundries) == 1:
                # All same version and foundry - use summary format
                version = list(versions)[0]
                foundry = list(foundries)[0]
                summary_reason = f"All RC extraction is used Quantus version {version} (Foundry: {foundry})"
                # Replace found_items with single summary entry
                # Use summary_reason as key so it displays as name
                found_items = {
                    summary_reason: {
                        'name': summary_reason,
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': ''  # Empty reason to avoid duplicate
                    }
                }
            else:
                # Different versions/foundries - use version as key for display
                new_found_items = {}
                for file_name, metadata in found_items.items():
                    version = metadata.get('version', 'N/A')
                    foundry = metadata.get('foundry', 'N/A')
                    # Format: "Quantus version X.Y.Z: filename (Foundry: F)"
                    display_name = f"Quantus version {version}: {file_name} (Foundry: {foundry})"
                    new_found_items[display_name] = {
                        'name': display_name,
                        'line_number': metadata.get('line_number', 0),
                        'file_path': metadata.get('file_path', 'N/A'),
                        'reason': ''  # Empty reason to avoid duplicate
                    }
                found_items = new_found_items
        
        # Use template helper - Type 1: Use TYPE1_4 reason (emphasize "found/not found") - API-025
        # Use lambda to generate custom reason from metadata (per README Display Format)
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=lambda m: m.get('reason', self.FOUND_REASON_TYPE1_4),
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check (status_check mode).
        
        Check if SPEF files use Quantus versions specified in pattern_items.
        pattern_items = Quantus VERSION NUMBERS to validate (e.g., "22.1.1-s233")
        
        Returns:
            CheckResult with is_pass based on version validation
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get requirements - pattern_items are Quantus VERSION NUMBERS to check
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # status_check mode: Check if SPEF files use versions matching pattern_items
        found_items = {}      # Version matches pattern_items (or >= pattern version)
        missing_items = {}    # Version doesn't match pattern_items
        
        for spef_data in items:
            file_name = spef_data['file_name']
            quantus_version = spef_data.get('quantus_version')
            foundry = spef_data.get('foundry', 'Unknown')
            line_number = spef_data.get('line_number', 0)
            file_path = spef_data.get('file_path', 'N/A')
            
            if not quantus_version:
                # Missing version info
                display_name = f"VERSION header not found: {file_name}"
                missing_items[display_name] = {
                    'name': display_name,
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': ''
                }
                continue
            
            # Type 2: Check if version matches any pattern_item
            version_ok = False
            matched_pattern = None
            
            if not pattern_items:
                # No pattern_items configured - report as error
                display_name = f"No pattern_items configured for version validation"
                missing_items[display_name] = {
                    'name': display_name,
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': ''
                }
                break
            
            # Check against pattern_items (expected versions)
            for pattern_version in pattern_items:
                # Check exact match or version >= pattern
                if quantus_version == pattern_version:
                    version_ok = True
                    matched_pattern = pattern_version
                    break
                # Also accept if extracted version >= required pattern version
                comparison = self._compare_versions(quantus_version, pattern_version)
                if comparison >= 0:
                    version_ok = True
                    matched_pattern = pattern_version
                    break
            
            # Format display name per README
            if version_ok:
                display_name = f"Quantus version {quantus_version}: {file_name} (Foundry: {foundry})"
                found_items[display_name] = {
                    'name': display_name,
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': '',
                    'version': quantus_version,
                    'foundry': foundry
                }
            else:
                # Version doesn't match - show required version from pattern_items
                required = pattern_items[0] if pattern_items else 'N/A'
                display_name = f"Quantus version {quantus_version}: {file_name} - Found version {quantus_version}, Required version >={required} (Foundry: {foundry})"
                missing_items[display_name] = {
                    'name': display_name,
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': ''
                }
        
        # Apply README Display Format for found_items (same as Type 1)
        if found_items:
            versions = set(m.get('version') for m in found_items.values() if m.get('version'))
            foundries = set(m.get('foundry') for m in found_items.values() if m.get('foundry'))
            
            if len(versions) == 1 and len(foundries) == 1:
                # All same version and foundry - use summary format
                version = list(versions)[0]
                foundry = list(foundries)[0]
                summary = f"All RC extraction is used Quantus version {version} (Foundry: {foundry})"
                found_items = {summary: {'name': summary, 'line_number': 0, 'file_path': 'N/A', 'reason': ''}}
        
        # Use template helper
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items if missing_items else [],
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=lambda m: m.get('reason', ''),
            missing_reason=lambda m: m.get('reason', '')
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support (status_check mode).
        
        Same logic as Type 2, plus waiver classification.
        pattern_items = Quantus VERSION NUMBERS to validate
        Waiver matches against Quantus VERSION NUMBERS (not filenames).
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        
        # Get waivers - waive_items.name = VERSION NUMBERS
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get pattern_items - expected VERSION NUMBERS
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        
        # Check each SPEF file
        found_items = {}      # Version correct
        waived_items = {}     # Version wrong AND waived (by version number)
        unwaived_items = {}   # Version wrong AND not waived
        
        for spef_data in items:
            file_name = spef_data['file_name']
            quantus_version = spef_data.get('quantus_version')
            foundry = spef_data.get('foundry', 'Unknown')
            line_number = spef_data.get('line_number', 0)
            file_path = spef_data.get('file_path', 'N/A')
            
            if not quantus_version:
                # Missing version - check waiver by filename (fallback)
                display_name = f"VERSION header not found: {file_name}"
                if self.match_waiver_entry(file_name, waive_dict):
                    waived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                else:
                    unwaived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                continue
            
            # Type 3: Check if version matches pattern_items
            version_ok = False
            required_version = None
            
            if not pattern_items:
                # No pattern_items configured - treat as version issue
                required_version = 'N/A'
                version_ok = False
            else:
                for pattern_version in pattern_items:
                    if quantus_version == pattern_version:
                        version_ok = True
                        required_version = pattern_version
                        break
                    comparison = self._compare_versions(quantus_version, pattern_version)
                    if comparison >= 0:
                        version_ok = True
                        required_version = pattern_version
                        break
                if not required_version:
                    required_version = pattern_items[0]
            
            if version_ok:
                # Version correct
                display_name = f"Quantus version {quantus_version}: {file_name} (Foundry: {foundry})"
                found_items[display_name] = {
                    'name': display_name,
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': '',
                    'version': quantus_version,
                    'foundry': foundry
                }
            else:
                # Version wrong - check waiver by VERSION NUMBER (per README)
                display_name = f"Quantus version {quantus_version}: {file_name} - Found version {quantus_version}, Required version >={required_version} (Foundry: {foundry})"
                if self.match_waiver_entry(quantus_version, waive_dict):
                    waived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                else:
                    unwaived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
        
        # Find unused waivers - match against version numbers used
        used_versions = set()
        for name in waived_items.keys():
            # Extract version from display_name "Quantus version X.Y.Z: ..."
            if 'Quantus version' in name:
                parts = name.split(':')[0].replace('Quantus version ', '')
                used_versions.add(parts.strip())
        unused_waivers = {name: {} for name in waive_dict.keys() if name not in used_versions}
        
        # Apply README Display Format for found_items
        if found_items:
            versions = set(m.get('version') for m in found_items.values() if m.get('version'))
            foundries = set(m.get('foundry') for m in found_items.values() if m.get('foundry'))
            
            if len(versions) == 1 and len(foundries) == 1:
                version = list(versions)[0]
                foundry = list(foundries)[0]
                summary = f"All RC extraction is used Quantus version {version} (Foundry: {foundry})"
                found_items = {summary: {'name': summary, 'line_number': 0, 'file_path': 'N/A', 'reason': ''}}
        
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda m: m.get('reason', ''),
            missing_reason=lambda m: m.get('reason', ''),
            waived_base_reason=self.WAIVED_BASE_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        Waiver matches against Quantus VERSION NUMBERS (not filenames).
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        
        # Get waivers - waive_items.name = VERSION NUMBERS
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check each SPEF file
        found_items = {}      # Version correct
        waived_items = {}     # Version wrong AND waived (by version number)
        unwaived_items = {}   # Version wrong AND not waived
        
        for spef_data in items:
            file_name = spef_data['file_name']
            quantus_version = spef_data.get('quantus_version')
            foundry = spef_data.get('foundry', 'Unknown')
            line_number = spef_data.get('line_number', 0)
            file_path = spef_data.get('file_path', 'N/A')
            
            if not quantus_version:
                # Missing version - check waiver by filename (fallback)
                display_name = f"VERSION header not found: {file_name}"
                if self.match_waiver_entry(file_name, waive_dict):
                    waived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                else:
                    unwaived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                continue
            
            if not foundry or foundry == 'Unknown':
                # Missing foundry - check waiver
                display_name = f"Cannot identify foundry: {file_name}"
                if self.match_waiver_entry(file_name, waive_dict):
                    waived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                else:
                    unwaived_items[display_name] = {
                        'name': display_name,
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': ''
                    }
                continue
            
            # Type 4: Boolean check - version info exists
            display_name = f"Quantus version {quantus_version}: {file_name} (Foundry: {foundry})"
            found_items[display_name] = {
                'name': display_name,
                'line_number': line_number,
                'file_path': file_path,
                'reason': '',
                'version': quantus_version,
                'foundry': foundry
            }
        
        # Find unused waivers - match against version numbers used
        used_versions = set()
        for name in waived_items.keys():
            if 'Quantus version' in name:
                parts = name.split(':')[0].replace('Quantus version ', '')
                used_versions.add(parts.strip())
        unused_waivers = {name: {} for name in waive_dict.keys() if name not in used_versions}
        
        # Apply README Display Format for found_items
        if found_items:
            versions = set(m.get('version') for m in found_items.values() if m.get('version'))
            foundries = set(m.get('foundry') for m in found_items.values() if m.get('foundry'))
            
            if len(versions) == 1 and len(foundries) == 1:
                version = list(versions)[0]
                foundry = list(foundries)[0]
                summary = f"All RC extraction is used Quantus version {version} (Foundry: {foundry})"
                found_items = {summary: {'name': summary, 'line_number': 0, 'file_path': 'N/A', 'reason': ''}}
        
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            has_waiver_value=True,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=lambda m: m.get('reason', ''),
            missing_reason=lambda m: m.get('reason', ''),
            waived_base_reason=self.WAIVED_BASE_REASON
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_9_0_0_05()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())