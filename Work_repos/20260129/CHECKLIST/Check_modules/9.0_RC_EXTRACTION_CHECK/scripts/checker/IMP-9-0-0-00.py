################################################################################
# Script Name: IMP-9-0-0-00.py
#
# Purpose:
#   Confirm SPEF extaction includes dummy metal gds.
#
# Logic:
#   - Parse input files: all QRC extraction log files in logs/9.0/ directory
#   - Search for 'input_db -type metal_fill' configuration with -gds_file parameter
#   - Extract GDS file path and verify it contains "BEOL" substring
#   - Search for 'metal_fill -type' to get processing mode (FLOATING/GROUNDED/NONE)
#   - Scan for ERROR/WARNING messages containing metal_fill, MetalFill, gds_file, BEOL keywords
#   - Search for standalone message "does NOT contain MetalFill data" (critical error)
#   - Verify metal fill is included: FLOATING/GROUNDED = PASS, NONE/missing = FAIL
#   - Aggregate results across all extraction corner logs
#   - Report PASS if all logs have valid metal fill configuration, FAIL if any missing
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, pattern_items [] (empty), waivers.value=N/A/0 → Boolean Check
#   Type 2: requirements.value>0, pattern_items [...] (defined), waivers.value=N/A/0 → Value Check
#   Type 3: requirements.value>0, pattern_items [...] (defined), waivers.value>0 → Value Check with Waiver Logic
#   Type 4: requirements.value=N/A, pattern_items [] (empty), waivers.value>0 → Boolean Check with Waiver Logic
#   Note: requirements.value indicates number of patterns for config validation (doesn't affect PASS/FAIL)
#
# Waiver Tag Rules:
#   When waivers.value > 0 (Type 3/4):
#     - All waive_items related INFO/FAIL/WARN reason suffix: [WAIVER]
#   When waivers.value = 0 (Type 1/2):
#     - waive_items output as INFO with suffix: [WAIVED_INFO]
#     - FAIL/WARN converted to INFO with suffix: [WAIVED_AS_INFO]
#   All types support value = N/A
#
# Refactored: 2026-01-06 (Using checker_templates v1.1.0)
#
# Author: Muhan Xing
# Date: 2026-01-06
################################################################################

from pathlib import Path
import re
import sys
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
from checker_templates.input_file_parser_template import InputFileParserMixin  # Optional but recommended


# MANDATORY: Inherit mixins in correct order (InputFileParserMixin first if used)
class Check_9_0_0_00(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-9-0-0-00: Confirm SPEF extaction includes dummy metal gds.
    
    Checking Types:
    - Type 1: requirements=N/A, pattern_items [], waivers=N/A/0 → Boolean Check
    - Type 2: requirements>0, pattern_items [...], waivers=N/A/0 → Value Check
    - Type 3: requirements>0, pattern_items [...], waivers>0 → Value Check with Waiver Logic
    - Type 4: requirements=N/A, pattern_items [], waivers>0 → Boolean Check with Waiver Logic
    
    Template Library v1.1.0:
    - Uses InputFileParserMixin for parsing (parse_log_with_patterns, normalize_command)
    - Uses WaiverHandlerMixin for waiver processing (parse_waive_items(waive_items_raw), match_waiver_entry(item, waive_dict))
    - Uses OutputBuilderMixin for result construction (build_complete_output(...))
    """
    
    # =========================================================================
    # ⭐ DESCRIPTION CONSTANTS - Split by Type semantics (API-026)
    # =========================================================================
    # DESC constants are split by Type for semantic clarity (same as REASON split)
    # Type 1/4 emphasize "found/not found", Type 2/3 emphasize "matched/satisfied"
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_DESC_TYPE1_4 = "QRC extraction completed with metal fill GDS configuration found"
    MISSING_DESC_TYPE1_4 = "QRC extraction missing metal fill GDS configuration or contains errors"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Metal fill GDS configuration matched and validated in extraction corner logs"
    MISSING_DESC_TYPE2_3 = "Expected metal fill GDS configuration not satisfied or missing in extraction corner logs"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Metal fill configuration errors waived per project requirements"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Metal fill GDS file found in extraction corner configuration with valid BEOL path"
    MISSING_REASON_TYPE1_4 = "Metal fill GDS configuration not found or contains critical errors (missing MetalFill data) in this corner"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "Metal fill configuration pattern matched with FLOATING/GROUNDED type and valid GDS path"
    MISSING_REASON_TYPE2_3 = "Expected metal fill pattern not satisfied: missing input_db configuration or type is NONE in this corner"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Metal fill configuration error waived for this extraction corner"
    UNUSED_WAIVER_REASON = "Waiver defined but no metal fill violation matched"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="9.0_RC_EXTRACTION_CHECK",
            item_id="IMP-9-0-0-00",
            item_desc="Confirm SPEF extaction includes dummy metal gds."
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
    
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
    
    def _get_all_log_files(self) -> List[Path]:
        """
        Get QRC extraction log files from input_files configuration.
        
        Returns:
            List of Path objects for configured input log files
        """
        input_files = self.item_data.get('input_files', [])
        log_files = []
        
        for file_entry in input_files:
            # Handle both absolute paths and relative paths with variable substitution
            file_entry_str = str(file_entry)
            
            # Replace ${CHECKLIST_ROOT} with actual root path
            if '${CHECKLIST_ROOT}' in file_entry_str:
                file_entry_str = file_entry_str.replace('${CHECKLIST_ROOT}', str(self.root))
            
            file_path = Path(file_entry_str)
            
            # If path is not absolute, treat as relative to root/IP_project_folder
            if not file_path.is_absolute():
                file_path = self.root / 'IP_project_folder' / file_entry_str
            
            if file_path.exists():
                log_files.append(file_path)
        
        return log_files
    
    def _parse_input_files(self) -> Dict[str, Any]:
        """
        Parse input files to extract metal fill configuration data.
        
        Parses QRC extraction log files specified in input_files to verify:
        1. input_db -type metal_fill configuration with -gds_file parameter
        2. GDS file path contains "BEOL" substring
        3. metal_fill -type is FLOATING or GROUNDED (not NONE)
        4. No ERROR messages about missing MetalFill data
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Metal fill configurations found (with metadata)
            - 'errors': List[Dict] - Error messages related to metal fill
            - 'metadata': Dict - File metadata (corners processed, etc.)
        """
        # Get log files from input_files configuration
        all_log_files = self._get_all_log_files()
        
        if not all_log_files or len(all_log_files) == 0:
            raise ConfigurationError(
                self.create_missing_files_error(["No log files found in input_files configuration"])
            )
        
        # 2. Parse using patterns from file analysis
        all_items = []
        all_errors = []
        corners_processed = []
        corner_file_map = {}  # Map corner name to file path
        
        # Define patterns for metal fill detection
        # Pattern 1: Metal fill GDS input configuration (multi-line)
        # Support both single-line and multi-line formats (path may be on next line)
        pattern_metal_fill_gds = re.compile(
            r'input_db\s+-type\s+metal_fill\s+.*?-gds_file\s*=?\s*"([^"]+)"',
            re.MULTILINE | re.DOTALL
        )
        
        # Pattern 2: Metal fill type configuration
        pattern_metal_fill_type = re.compile(
            r'^metal_fill\s+.*?-type\s+"([^"]+)"',
            re.MULTILINE | re.DOTALL
        )
        pattern_enable_metal_fill = re.compile(
            r'enable_metal_fill_effects\s*=\s*"(true)"',
            re.IGNORECASE
        )
        
        # Pattern 3: Error messages related to metal fill
        pattern_error = re.compile(
            r'^(?:ERROR|\*\*ERROR).*?(?:metal_fill|MetalFill|gds_file|BEOL).*$',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Pattern 4: Warning messages about metal fill processing
        pattern_warning = re.compile(
            r'^(?:WARNING|\*\*WARNING).*?(?:metal_fill|gds|density).*$',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Pattern 5: Missing MetalFill data message (standalone, critical)
        pattern_missing_metalfill = re.compile(
            r'does NOT contain MetalFill data',
            re.IGNORECASE
        )
        
        for file_path in all_log_files:
            corner_name = file_path.stem  # Extract corner name from filename
            corners_processed.append(corner_name)
            corner_file_map[corner_name] = str(file_path)  # Store the mapping
            
            # Read entire file for multi-line pattern matching
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
            except Exception as e:
                all_errors.append({
                    'name': f"File read error: {file_path.name}",
                    'line_number': 0,
                    'file_path': str(file_path),
                    'error': str(e)
                })
                continue
            
            # Print gds file to Metal fill GDS mapping
            print(f"\n{'='*80}")
            print(f"Processing log file: {file_path.name}")
            print(f"Corner: {corner_name}")
            print(f"{'='*80}")
            
            # Search for metal fill GDS configuration
            gds_matches = pattern_metal_fill_gds.finditer(content)
            gds_found = False
            for match in gds_matches:
                gds_file_path = match.group(1)
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                
                # Print the mapping
                print(f"\nMetal fill GDS configuration found:")
                print(f"  GDS file: {gds_file_path}")
                print(f"  Line number: {line_num}")
                
                # Verify path contains "BEOL"
                has_beol = 'BEOL' in gds_file_path or 'beol' in gds_file_path.lower()
                print(f"  Contains BEOL: {has_beol}")
                
                # Output GDS path in requested format - ANSWER TO USER'S QUESTION
                # Extract just the filename without directory path
                gds_filename = Path(gds_file_path).name
                print(f"\n[BEOL_GDS_PATH] Corner={corner_name}, Path={gds_filename}")
                
                all_items.append({
                    'name': f"{corner_name}: Metal fill GDS ({gds_filename})",
                    'gds_path': gds_file_path,
                    'has_beol': has_beol,
                    'line_number': line_num,
                    'file_path': str(file_path),
                    'corner': corner_name
                })
                gds_found = True
            
            if not gds_found:
                print(f"\nWARNING: No metal fill GDS configuration found in {corner_name}")
            
            # Search for metal fill type or enable_metal_fill_effects
            type_matches = pattern_metal_fill_type.finditer(content)
            enable_matches = pattern_enable_metal_fill.finditer(content)
            type_found = False
            
            # First check for explicit metal_fill -type configuration
            for match in type_matches:
                metal_fill_type = match.group(1)
                line_num = content[:match.start()].count('\n') + 1
                
                print(f"\nMetal fill type configuration found:")
                print(f"  Type: {metal_fill_type}")
                print(f"  Line number: {line_num}")
                
                # Update existing item or create new one
                corner_item = next(
                    (item for item in all_items if item.get('corner') == corner_name and 'gds_path' in item),
                    None
                )
                if corner_item:
                    corner_item['metal_fill_type'] = metal_fill_type
                else:
                    all_items.append({
                        'name': f"{corner_name}: Metal fill type",
                        'metal_fill_type': metal_fill_type,
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'corner': corner_name
                    })
                type_found = True
            
            # If no explicit type, check for enable_metal_fill_effects = true
            if not type_found:
                for match in enable_matches:
                    enable_value = match.group(1)
                    line_num = content[:match.start()].count('\n') + 1
                    
                    print(f"\nMetal fill enabled via enable_metal_fill_effects:")
                    print(f"  Value: {enable_value}")
                    print(f"  Line number: {line_num}")
                    
                    all_items.append({
                        'name': f"{corner_name}: Metal fill enabled",
                        'metal_fill_type': 'ENABLED',
                        'line_number': line_num,
                        'file_path': str(file_path),
                        'corner': corner_name
                    })
                    type_found = True
                    break
            
            if not type_found:
                print(f"\nWARNING: No metal fill type configuration found in {corner_name}")
            
            # Search for ERROR messages
            error_matches = pattern_error.finditer(content)
            for match in error_matches:
                line_num = content[:match.start()].count('\n') + 1
                error_msg = match.group(0).strip()
                print(f"\nERROR found:")
                print(f"  Message: {error_msg}")
                print(f"  Line number: {line_num}")
                all_errors.append({
                    'name': f"{corner_name}: Metal fill error",
                    'error_message': error_msg,
                    'line_number': line_num,
                    'file_path': str(file_path),
                    'corner': corner_name
                })
            
            # Search for WARNING messages
            warning_matches = pattern_warning.finditer(content)
            for match in warning_matches:
                line_num = content[:match.start()].count('\n') + 1
                warning_msg = match.group(0).strip()
                print(f"\nWARNING found:")
                print(f"  Message: {warning_msg}")
                print(f"  Line number: {line_num}")
                # Warnings are informational, not critical errors
                all_items.append({
                    'name': f"{corner_name}: Metal fill warning",
                    'warning_message': warning_msg,
                    'line_number': line_num,
                    'file_path': str(file_path),
                    'corner': corner_name,
                    'is_warning': True
                })
            
            # Search for critical "does NOT contain MetalFill data" message
            missing_metalfill_matches = pattern_missing_metalfill.finditer(content)
            for match in missing_metalfill_matches:
                line_num = content[:match.start()].count('\n') + 1
                error_msg = lines[line_num - 1].strip() if line_num <= len(lines) else match.group(0)
                print(f"\nCRITICAL ERROR found:")
                print(f"  Message: {error_msg}")
                print(f"  Line number: {line_num}")
                # This is a critical error
                all_errors.append({
                    'name': f"{corner_name}: Missing MetalFill data",
                    'error_message': error_msg,
                    'line_number': line_num,
                    'file_path': str(file_path),
                    'corner': corner_name,
                    'is_critical': True
                })
        
        print(f"\n{'='*80}")
        print(f"Summary: Processed {len(corners_processed)} corner(s)")
        print(f"Total items found: {len(all_items)}")
        print(f"Total errors found: {len(all_errors)}")
        
        # Print detailed summary of found items
        print(f"\nDetailed Summary:")
        for corner in corners_processed:
            corner_items = [item for item in all_items if item.get('corner') == corner and not item.get('is_warning', False)]
            corner_errors = [error for error in all_errors if error.get('corner') == corner]
            
            print(f"\n  Corner: {corner}")
            print(f"    Items found: {len(corner_items)}")
            
            # Check for GDS configuration
            gds_items = [item for item in corner_items if 'gds_path' in item]
            if gds_items:
                for item in gds_items:
                    gds_path = item.get('gds_path', 'N/A')
                    gds_filename = Path(gds_path).name
                    print(f"      - GDS file: {gds_filename}")
                    print(f"        Full path: {gds_path}")
                    print(f"        Has BEOL: {item.get('has_beol', False)}")
                    # Output GDS file path in requested format
                    print(f"      - {corner}: Metal fill GDS path: {gds_path}")
            else:
                print(f"      - No GDS configuration found")
            
            # Check for metal fill type
            type_items = [item for item in corner_items if 'metal_fill_type' in item]
            if type_items:
                for item in type_items:
                    print(f"      - Metal fill type: {item.get('metal_fill_type', 'N/A')}")
            else:
                print(f"      - No metal fill type found")
            
            # Check for errors
            if corner_errors:
                print(f"    Errors: {len(corner_errors)}")
                for error in corner_errors:
                    print(f"      - {error.get('error_message', 'Unknown error')}")
            else:
                print(f"    Errors: 0")
        
        print(f"{'='*80}\n")
        
        # 3. Store on self
        self._parsed_items = all_items
        self._metadata = {
            'corners_processed': corners_processed,
            'corner_file_map': corner_file_map,
            'total_corners': len(corners_processed)
        }
        
        # 4. Return aggregated dict
        return {
            'items': all_items,
            'errors': all_errors,
            'metadata': self._metadata
        }
    
    # =========================================================================
    # Type 1: Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean Check.
        
        Verifies that metal fill GDS configuration exists in all extraction corner logs.
        PASS if all corners have valid metal fill configuration.
        FAIL if any corner is missing metal fill or has errors.
        
        Returns:
            CheckResult with is_pass based on check logic
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})
        
        # Build corner-level configuration map
        corners_with_metalfill = {}
        found_items = {}
        
        for item in items:
            if not item.get('is_warning', False):  # Skip warnings
                corner = item.get('corner', 'unknown')
                
                # Check if configuration is valid
                has_gds = 'gds_path' in item
                has_beol = item.get('has_beol', False)
                metal_fill_type = item.get('metal_fill_type', '')
                is_valid_type = metal_fill_type in ['FLOATING', 'GROUNDED', 'ENABLED']
                
                if has_gds and has_beol:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': True,
                            'has_beol': True,
                            'has_type': False,
                            'is_valid_type': False,
                            'gds_path': item.get('gds_path', ''),
                            'gds_name': Path(item.get('gds_path', '')).name,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Update GDS info but preserve type information if already set
                        corners_with_metalfill[corner]['has_gds'] = True
                        corners_with_metalfill[corner]['has_beol'] = True
                        corners_with_metalfill[corner]['gds_path'] = item.get('gds_path', '')
                        corners_with_metalfill[corner]['gds_name'] = Path(item.get('gds_path', '')).name
                        corners_with_metalfill[corner]['line_number'] = item.get('line_number', 0)
                
                if metal_fill_type:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': False,
                            'has_beol': False,
                            'has_type': True,
                            'is_valid_type': is_valid_type,
                            'metal_fill_type': metal_fill_type,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        corners_with_metalfill[corner]['has_type'] = True
                        corners_with_metalfill[corner]['is_valid_type'] = is_valid_type
                        corners_with_metalfill[corner]['metal_fill_type'] = metal_fill_type
        
        # Build found_items for corners with complete valid configuration
        for corner, config in corners_with_metalfill.items():
            if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']:
                # Extract GDS path for display (full path)
                gds_path = config.get('gds_path', 'N/A')
                gds_name = config.get('gds_name', 'N/A')
                # Use full path in the key for proper display in output
                found_items[f"{corner}.log: Metal fill GDS = {gds_path}"] = {
                    'value': gds_path,
                    'line_number': config['line_number'],
                    'file_path': config['file_path']
                }
        
        # Check for errors
        missing_items = []
        if errors:
            for error in errors:
                missing_items.append(error['name'])
        
        # Check if all corners have metal fill
        total_corners = metadata.get('total_corners', 0)
        corners_with_valid_config = set(
            corner for corner, config in corners_with_metalfill.items()
            if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']
        )
        
        if len(corners_with_valid_config) < total_corners:
            missing_corners = set(metadata.get('corners_processed', [])) - corners_with_valid_config
            corner_file_map = metadata.get('corner_file_map', {})
            for corner in missing_corners:
                file_path = corner_file_map.get(corner, 'Unknown path')
                missing_items.append(f"{corner}.log: Metal fill configuration missing or incomplete. In {file_path}")
        
        # Use template helper
        # Type 1: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )
    
    # =========================================================================
    # Type 2: Value Check
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value Check.
        
        Search pattern_items in input files across all corners.
        found_items = patterns found; missing_items = patterns not found.
        
        Returns:
            CheckResult with is_pass based on value comparison
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        metadata = data.get('metadata', {})
        
        # Build corner-level configuration map
        corners_with_metalfill = {}
        
        for item in items:
            if not item.get('is_warning', False):  # Skip warnings
                corner = item.get('corner', 'unknown')
                
                # Check if configuration is valid
                has_gds = 'gds_path' in item
                has_beol = item.get('has_beol', False)
                metal_fill_type = item.get('metal_fill_type', '')
                is_valid_type = metal_fill_type in ['FLOATING', 'GROUNDED', 'ENABLED']
                
                if has_gds and has_beol:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': True,
                            'has_beol': True,
                            'has_type': False,
                            'is_valid_type': False,
                            'gds_path': item.get('gds_path', ''),
                            'gds_name': Path(item.get('gds_path', '')).name,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Update GDS info but preserve type information if already set
                        corners_with_metalfill[corner]['has_gds'] = True
                        corners_with_metalfill[corner]['has_beol'] = True
                        corners_with_metalfill[corner]['gds_path'] = item.get('gds_path', '')
                        corners_with_metalfill[corner]['gds_name'] = Path(item.get('gds_path', '')).name
                        corners_with_metalfill[corner]['line_number'] = item.get('line_number', 0)
                
                if metal_fill_type:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': False,
                            'has_beol': False,
                            'has_type': True,
                            'is_valid_type': is_valid_type,
                            'metal_fill_type': metal_fill_type,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        corners_with_metalfill[corner]['has_type'] = True
                        corners_with_metalfill[corner]['is_valid_type'] = is_valid_type
                        corners_with_metalfill[corner]['metal_fill_type'] = metal_fill_type
        
        # Find which patterns exist in parsed items
        found_items = {}
        missing_items = []
        
        # For Type 2, if pattern_items is empty, check all corners
        if not pattern_items:
            # No specific patterns, check all corners for valid configuration
            for corner, config in corners_with_metalfill.items():
                if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']:
                    gds_path = config.get('gds_path', 'N/A')
                    found_items[f"{corner}.log: Metal fill GDS = {gds_path}"] = {
                        'value': gds_path,
                        'line_number': config['line_number'],
                        'file_path': config['file_path']
                    }
        else:
            # Match patterns against corners
            for pattern in pattern_items:
                matched = False
                # Remove .log extension from pattern if present for matching
                pattern_name = pattern.replace('.log', '') if pattern.endswith('.log') else pattern
                
                for corner, config in corners_with_metalfill.items():
                    # Match pattern against corner name
                    if pattern_name.lower() in corner.lower():
                        # Verify configuration is valid
                        if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']:
                            gds_path = config.get('gds_path', 'N/A')
                            found_items[f"{corner}.log: Metal fill GDS = {gds_path}"] = {
                                'value': gds_path,
                                'line_number': config['line_number'],
                                'file_path': config['file_path']
                            }
                            matched = True
                            break
                
                if not matched:
                    # Try to find the file path for this pattern
                    corner_file_map = metadata.get('corner_file_map', {})
                    pattern_base = pattern.replace('.log', '') if pattern.endswith('.log') else pattern
                    file_path = corner_file_map.get(pattern_base, 'Unknown path')
                    missing_items.append(f"{pattern}: Pattern not found. In {file_path}")
        
        # Add errors to missing items with detailed fail reasons (only if they are actual errors)
        # For Type 2, we should NOT add errors if the log has both input_db and metal_fill configurations
        for error in errors:
            # Check if this error's corner has valid configuration
            error_corner = error.get('corner', 'unknown')
            corner_config = corners_with_metalfill.get(error_corner, {})
            
            # Only add error if corner doesn't have complete valid configuration
            if not (corner_config.get('has_gds') and corner_config.get('has_beol') and 
                    corner_config.get('has_type') and corner_config.get('is_valid_type')):
                fail_reason = error.get('fail_reason', f"{error['name']}: {error.get('error_message', 'Unknown error')}")
                if fail_reason not in missing_items:
                    missing_items.append(fail_reason)
        
        # Use template helper (auto-handles waiver=0)
        # Type 2: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support.
        
        Same pattern search logic as Type 2, plus waiver classification.
        Checks all corners for pattern matches.
        
        Returns:
            CheckResult with FAIL for unwaived, INFO for waived items
        """
        # Parse input
        parsed_data = self._parse_input_files()
        items = parsed_data.get('items', [])
        errors = parsed_data.get('errors', [])
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Get requirements
        pattern_items = self.item_data.get('requirements', {}).get('pattern_items', [])
        metadata = parsed_data.get('metadata', {})
        
        # Build corner-level configuration map
        corners_with_metalfill = {}
        
        for item in items:
            if not item.get('is_warning', False):  # Skip warnings
                corner = item.get('corner', 'unknown')
                
                # Check if configuration is valid
                has_gds = 'gds_path' in item
                has_beol = item.get('has_beol', False)
                metal_fill_type = item.get('metal_fill_type', '')
                is_valid_type = metal_fill_type in ['FLOATING', 'GROUNDED', 'ENABLED']
                
                if has_gds and has_beol:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': True,
                            'has_beol': True,
                            'has_type': False,
                            'is_valid_type': False,
                            'gds_path': item.get('gds_path', ''),
                            'gds_name': Path(item.get('gds_path', '')).name,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Update GDS info but preserve type information if already set
                        corners_with_metalfill[corner]['has_gds'] = True
                        corners_with_metalfill[corner]['has_beol'] = True
                        corners_with_metalfill[corner]['gds_path'] = item.get('gds_path', '')
                        corners_with_metalfill[corner]['gds_name'] = Path(item.get('gds_path', '')).name
                        corners_with_metalfill[corner]['line_number'] = item.get('line_number', 0)
                
                if metal_fill_type:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': False,
                            'has_beol': False,
                            'has_type': True,
                            'is_valid_type': is_valid_type,
                            'metal_fill_type': metal_fill_type,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        corners_with_metalfill[corner]['has_type'] = True
                        corners_with_metalfill[corner]['is_valid_type'] = is_valid_type
                        corners_with_metalfill[corner]['metal_fill_type'] = metal_fill_type
        
        # Find which patterns exist and are valid
        found_items = {}
        violations = []
        
        for pattern in pattern_items:
            matched = False
            # Remove .log extension from pattern if present for matching
            pattern_name = pattern.replace('.log', '') if pattern.endswith('.log') else pattern
            
            for corner, config in corners_with_metalfill.items():
                # Match pattern against corner name
                if pattern_name.lower() in corner.lower():
                    # Verify configuration is valid
                    if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']:
                        gds_path = config.get('gds_path', 'N/A')
                        found_items[f"{corner}.log: Metal fill GDS = {gds_path}"] = {
                            'value': gds_path,
                            'line_number': config['line_number'],
                            'file_path': config['file_path']
                        }
                        matched = True
                        break
            
            if not matched:
                # Try to find the file path for this pattern
                corner_file_map = metadata.get('corner_file_map', {})
                pattern_base = pattern.replace('.log', '') if pattern.endswith('.log') else pattern
                file_path = corner_file_map.get(pattern_base, 'Unknown path')
                violations.append(f"{pattern}: Pattern not found. In {file_path}")
        
        # Add errors to violations (only if they are actual errors)
        for error in errors:
            # Check if this error's corner has valid configuration
            error_corner = error.get('corner', 'unknown')
            corner_config = corners_with_metalfill.get(error_corner, {})
            
            # Only add error if corner doesn't have complete valid configuration
            if not (corner_config.get('has_gds') and corner_config.get('has_beol') and 
                    corner_config.get('has_type') and corner_config.get('is_valid_type')):
                fail_reason = error.get('fail_reason', f"{error['name']}: {error.get('error_message', 'Unknown error')}")
                if fail_reason not in violations:
                    violations.append(fail_reason)
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        used_waiver_keys = set()
        
        for violation in violations:
            matched_key = self.match_waiver_entry(violation, waive_dict)
            if matched_key:
                waived_items.append(violation)
                used_waiver_keys.add(matched_key)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        unused_waivers = [name for name in waive_dict.keys() if name not in used_waiver_keys]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 3: Use TYPE2_3 desc+reason (emphasize "matched/satisfied") - API-026
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (Type 1 + waiver).
        
        Same boolean check as Type 1 (no pattern_items), plus waiver classification.
        Checks all corners for metal fill configuration.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])
        metadata = data.get('metadata', {})
        
        # Fix API-016: Use waivers.get() directly to preserve dict format
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', [])
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check if metal fill configuration exists for all corners
        corners_with_metalfill = {}
        found_items = {}
        violations = []
        
        for item in items:
            if not item.get('is_warning', False):  # Skip warnings
                corner = item.get('corner', 'unknown')
                
                # Check if configuration is valid
                has_gds = 'gds_path' in item
                has_beol = item.get('has_beol', False)
                metal_fill_type = item.get('metal_fill_type', '')
                is_valid_type = metal_fill_type in ['FLOATING', 'GROUNDED', 'ENABLED']
                
                if has_gds and has_beol:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': True,
                            'has_beol': True,
                            'has_type': False,
                            'is_valid_type': False,
                            'gds_path': item.get('gds_path', ''),
                            'gds_name': Path(item.get('gds_path', '')).name,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        # Update GDS info but preserve type information if already set
                        corners_with_metalfill[corner]['has_gds'] = True
                        corners_with_metalfill[corner]['has_beol'] = True
                        corners_with_metalfill[corner]['gds_path'] = item.get('gds_path', '')
                        corners_with_metalfill[corner]['gds_name'] = Path(item.get('gds_path', '')).name
                        corners_with_metalfill[corner]['line_number'] = item.get('line_number', 0)
                
                if metal_fill_type:
                    if corner not in corners_with_metalfill:
                        corners_with_metalfill[corner] = {
                            'has_gds': False,
                            'has_beol': False,
                            'has_type': True,
                            'is_valid_type': is_valid_type,
                            'metal_fill_type': metal_fill_type,
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A')
                        }
                    else:
                        corners_with_metalfill[corner]['has_type'] = True
                        corners_with_metalfill[corner]['is_valid_type'] = is_valid_type
                        corners_with_metalfill[corner]['metal_fill_type'] = metal_fill_type
        
        # Build found_items for corners with complete valid configuration
        for corner, config in corners_with_metalfill.items():
            if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']:
                # Extract GDS path for display (full path)
                gds_path = config.get('gds_path', 'N/A')
                gds_name = config.get('gds_name', 'N/A')
                # Use full path in the key for proper display in output
                found_items[f"{corner}.log: Metal fill GDS = {gds_path}"] = {
                    'value': gds_path,
                    'line_number': config['line_number'],
                    'file_path': config['file_path']
                }
        
        # Check for errors
        if errors:
            for error in errors:
                violations.append(error['name'])
        
        # Check if all corners have metal fill
        total_corners = metadata.get('total_corners', 0)
        corners_with_valid_config = set(
            corner for corner, config in corners_with_metalfill.items()
            if config['has_gds'] and config['has_beol'] and config['has_type'] and config['is_valid_type']
        )
        
        if len(corners_with_valid_config) < total_corners:
            missing_corners = set(metadata.get('corners_processed', [])) - corners_with_valid_config
            corner_file_map = metadata.get('corner_file_map', {})
            for corner in missing_corners:
                # Add .log extension for waiver matching and file path
                file_path = corner_file_map.get(corner, 'Unknown path')
                violations.append(f"{corner}.log: Metal fill configuration missing or incomplete. In {file_path}")
        
        # Separate waived/unwaived using template helper
        waived_items = []
        unwaived_items = []
        used_waiver_keys = set()
        
        for violation in violations:
            matched_key = self.match_waiver_entry(violation, waive_dict)
            if matched_key:
                waived_items.append(violation)
                used_waiver_keys.add(matched_key)
            else:
                unwaived_items.append(violation)
        
        # Find unused waivers
        unused_waivers = [name for name in waive_dict.keys() if name not in used_waiver_keys]
        
        # Use template helper for automatic output formatting (waivers.value>0)
        # Type 4: Use TYPE1_4 reason (emphasize "found/not found")
        return self.build_complete_output(
            found_items=found_items,
            waived_items=waived_items,
            missing_items=unwaived_items,
            waive_dict=waive_dict,
            unused_waivers=unused_waivers,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

# test modify type4 #
# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_9_0_0_00()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())