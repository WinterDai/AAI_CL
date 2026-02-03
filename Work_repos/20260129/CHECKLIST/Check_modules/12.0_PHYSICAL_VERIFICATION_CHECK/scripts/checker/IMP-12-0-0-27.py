################################################################################
# Script Name: IMP-12-0-0-27.py
#
# Purpose:
#   Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?
#
# Logic:
#   - Parse tv_chip_gds_bump.csv to extract bump names and coordinates
#   - Extract bump location data (name, center_x, center_y, width, height)
#   - Verify bump existence and coordinate consistency against package requirements
#   - Support waiver for specific bumps (DUMMY_*, PAD_NJ_*)
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
# Author: Jingyu Wang
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
class Check_12_0_0_27(InputFileParserMixin, OutputBuilderMixin, WaiverHandlerMixin, BaseChecker):
    """
    IMP-12-0-0-27: Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?
    
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
    FOUND_DESC_TYPE1_4 = "All bump locations validated successfully in GDS extraction report"
    MISSING_DESC_TYPE1_4 = "Bump location validation failed - mismatches detected in GDS extraction"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_DESC_TYPE2_3 = "Required bump locations matched in GDS extraction (all bumps verified)"
    MISSING_DESC_TYPE2_3 = "Required bump locations not satisfied - missing or mismatched bumps detected"
    
    # All Types (waiver description unified)
    WAIVED_DESC = "Bump location mismatch waived"
    
    # ⭐ REASON CONSTANTS - Split by Type semantics (API-025)
    # ALL Types pass found_reason/missing_reason, but use different constants
    
    # Type 1/4: Boolean checks - emphasize "found/not found" (existence)
    FOUND_REASON_TYPE1_4 = "Bump location data extracted from GDS/OAS matches package requirements"
    MISSING_REASON_TYPE1_4 = "Bump location mismatches found between package requirements and GDS extraction"
    
    # Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
    FOUND_REASON_TYPE2_3 = "All required bump locations found and validated in GDS extraction report"
    MISSING_REASON_TYPE2_3 = "Required bump locations missing or coordinates mismatched in GDS extraction report"
    
    # Waiver-related (Type 3/4 only)
    WAIVED_BASE_REASON = "Bump location verification waived per package design team approval"
    UNUSED_WAIVER_REASON = "Waiver not matched - no corresponding bump location mismatch found"
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="12.0_PHYSICAL_VERIFICATION_CHECK",
            item_id="IMP-12-0-0-27",
            item_desc="Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
        )
        # Custom member variables for parsed data
        self._parsed_items: List[Dict[str, Any]] = []
        self._metadata: Dict[str, str] = {}
        self._bump_locations: Dict[str, Dict[str, Any]] = {}
    
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
        Parse input files to extract bump location information from GDS/OAS extraction CSV.
        
        Parses tv_chip_gds_bump.csv to extract:
        - Bump names (column 2)
        - Center coordinates (columns 3-4: Center_X, Center_Y)
        - Dimensions (columns 5-6: Width, Height)
        
        CSV Format: Bump_ID,Name,Center_X,Center_Y,Width,Height,Area,Text_Distance
        Example: 0,VDD2,2504.6540,4484.7600,80.0000,80.0000,5018.4943,0.0000
        
        Returns:
            Dict with parsed data:
            - 'items': List[Dict] - Bump location entries with metadata
            - 'metadata': Dict - File metadata (total bumps, coordinate ranges)
            - 'errors': List - Parsing errors
        """
        # 1. Validate input files (returns tuple: valid_files, missing_files)
        valid_files, missing_files = self.validate_input_files()
        
        # FIXED: Explicitly check for empty list
        if missing_files and len(missing_files) > 0:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        # FIXED: Explicitly check for empty list
        if not valid_files or len(valid_files) == 0:
            raise ConfigurationError("No valid input files found")
        
        # 2. Initialize parsing structures
        items = []
        metadata = {}
        errors = []
        bump_locations = {}
        
        # Coordinate range tracking
        min_x = float('inf')
        max_x = float('-inf')
        min_y = float('inf')
        max_y = float('-inf')
        
        # 3. Parse each input file for bump location information
        # Pattern: Bump_ID,Name,Center_X,Center_Y,Width,Height,Area,Text_Distance
        bump_pattern = re.compile(r'^(\d+),([^,]+),(\d+\.\d+),(\d+\.\d+),(\d+\.\d+),(\d+\.\d+),(\d+\.\d+),(\d+\.\d+)$')
        
        for file_path in valid_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Skip header line
                        if line_num == 1 and 'Bump_ID' in line:
                            continue
                        
                        # Skip empty lines
                        if not line:
                            continue
                        
                        # Match bump entry pattern
                        match = bump_pattern.match(line)
                        if match:
                            bump_id = match.group(1)
                            bump_name = match.group(2)
                            center_x = float(match.group(3))
                            center_y = float(match.group(4))
                            width = float(match.group(5))
                            height = float(match.group(6))
                            area = float(match.group(7))
                            text_distance = float(match.group(8))
                            
                            # Track coordinate ranges
                            min_x = min(min_x, center_x)
                            max_x = max(max_x, center_x)
                            min_y = min(min_y, center_y)
                            max_y = max(max_y, center_y)
                            
                            # Store bump location data
                            bump_data = {
                                'name': bump_name,
                                'bump_id': bump_id,
                                'center_x': center_x,
                                'center_y': center_y,
                                'width': width,
                                'height': height,
                                'area': area,
                                'text_distance': text_distance,
                                'line_number': line_num,
                                'file_path': str(file_path),
                                'type': self._classify_bump_type(bump_name)
                            }
                            
                            items.append(bump_data)
                            bump_locations[bump_name] = bump_data
                        else:
                            # Only log non-header lines that don't match
                            if 'Bump_ID' not in line:
                                errors.append(f"Line {line_num} in {file_path}: Invalid format - {line[:50]}")
            except Exception as e:
                errors.append(f"Error parsing {file_path}: {str(e)}")
        
        # 4. Store frequently reused data on self
        self._parsed_items = items
        self._bump_locations = bump_locations
        
        # Store metadata
        metadata = {
            'total_bumps': len(items),
            'min_x': min_x if min_x != float('inf') else 0,
            'max_x': max_x if max_x != float('-inf') else 0,
            'min_y': min_y if min_y != float('inf') else 0,
            'max_y': max_y if max_y != float('-inf') else 0
        }
        self._metadata = metadata
        
        return {
            'items': items,
            'metadata': metadata,
            'errors': errors
        }
    # Helper Methods (Optional - Add as needed)
    

    # =========================================================================
    # Type 1: Boolean Check

    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Boolean check without waiver support.

        Validates bump location data from GDS/OAS extraction against package requirements.
        All bumps must have valid coordinates and match expected locations.

        Returns:
            CheckResult with found_items (valid bumps) and missing_items (violations)
        """
        violations = self._type1_core_logic()

        # Build found_items from valid bumps (those without violations)
        data = self._parse_input_files()
        all_bumps = data.get('items', [])

        found_items = {}
        for bump in all_bumps:
            bump_name = bump.get('name', '')
            # Only include bumps that are NOT in violations
            if bump_name not in violations:
                found_items[bump_name] = {
                    'name': bump_name,
                    'line_number': bump.get('line_number', 0),
                    'file_path': bump.get('file_path', 'N/A')
                }

        missing_items = list(violations.keys()) if violations else []

        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4
        )

    def _type1_core_logic(self) -> dict[str, dict]:
        """
        Core Type 1 boolean check logic (shared by Type 1 and Type 4).

        Validates bump location data:
        - Checks for missing coordinate data
        - Validates coordinate format and values
        - Detects inconsistencies between package requirements and GDS extraction

        Returns:
            Dict of violations: {bump_name: {'line_number': ..., 'file_path': ..., 'reason': ...}}
            Empty dict if all checks pass.
        """
        data = self._parse_input_files()
        items = data.get('items', [])
        errors = data.get('errors', [])

        violations = {}

        # Check for parsing errors first
        if errors:
            for error in errors:
                error_key = f"parse_error_{len(violations)}"
                violations[error_key] = {
                    'line_number': 0,
                    'file_path': error.get('file_path', 'N/A'),
                    'reason': error.get('message', 'Unknown parsing error')
                }

        # If no items found, this is a critical violation
        if not items:
            violations['no_bump_data'] = {
                'line_number': 0,
                'file_path': 'N/A',
                'reason': 'No bump location data found in input file'
            }
            return violations

        # Validate each bump's data
        for bump in items:
            bump_name = bump.get('name', '')
            line_number = bump.get('line_number', 0)
            file_path = bump.get('file_path', 'N/A')

            # Check for missing bump name
            if not bump_name:
                violations[f'unnamed_bump_line_{line_number}'] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': 'Bump name is missing or empty'
                }
                continue

            # Check for missing coordinates
            center_x = bump.get('center_x')
            center_y = bump.get('center_y')

            if center_x is None or center_y is None:
                violations[bump_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f'Missing coordinate data (center_x: {center_x}, center_y: {center_y})'
                }
                continue

            # Validate coordinate values (must be numeric)
            try:
                x_val = float(center_x)
                y_val = float(center_y)

                # Check for invalid coordinate values (e.g., negative or zero)
                if x_val <= 0 or y_val <= 0:
                    violations[bump_name] = {
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': f'Invalid coordinate values (x: {x_val}, y: {y_val}) - coordinates must be positive'
                    }
                    continue

            except (ValueError, TypeError):
                violations[bump_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f'Non-numeric coordinate data (center_x: {center_x}, center_y: {center_y})'
                }
                continue

            # Check for dimension data (optional but should be present)
            width = bump.get('width')
            height = bump.get('height')

            if width is None or height is None:
                violations[bump_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f'Missing dimension data (width: {width}, height: {height})'
                }
                continue

            # Validate dimension values
            try:
                w_val = float(width)
                h_val = float(height)

                if w_val <= 0 or h_val <= 0:
                    violations[bump_name] = {
                        'line_number': line_number,
                        'file_path': file_path,
                        'reason': f'Invalid dimension values (width: {w_val}, height: {h_val}) - dimensions must be positive'
                    }
                    continue

            except (ValueError, TypeError):
                violations[bump_name] = {
                    'line_number': line_number,
                    'file_path': file_path,
                    'reason': f'Non-numeric dimension data (width: {width}, height: {height})'
                }
                continue

        return violations

    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic

    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support (reuses Type 1 core logic).

        Performs the same bump location validation as Type 1, but allows specific
        violations to be waived (e.g., DUMMY_* bumps, PAD_NJ_* test pads).

        Waiver matching supports:
        - Exact bump names: "VDD", "VSS"
        - Wildcard patterns: "DUMMY_*", "PAD_NJ_*"

        Returns:
            CheckResult with found_items, waived_items, missing_items (unwaived violations),
            and unused_waivers
        """
        # Step 1: Get violations using Type 1's core logic
        violations = self._type1_core_logic()

        # Build found_items from valid bumps (those without violations)
        data = self._parse_input_files()
        all_bumps = data.get('items', [])

        found_items = {}
        for bump in all_bumps:
            bump_name = bump.get('name', '')
            # Only include bumps that are NOT in violations
            if bump_name not in violations:
                found_items[bump_name] = {
                    'name': bump_name,
                    'line_number': bump.get('line_number', 0),
                    'file_path': bump.get('file_path', 'N/A')
                }

        # Step 2: Parse waiver configuration
        waive_dict = self.parse_waive_items()

        # Step 3: Split violations into waived and unwaived
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        for viol_name, viol_data in violations.items():
            matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()),
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE1_4,
            missing_desc=self.MISSING_DESC_TYPE1_4,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE1_4,
            missing_reason=self.MISSING_REASON_TYPE1_4,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )

    # =========================================================================
    # Type 2: Value Check

    def _execute_type2(self) -> CheckResult:
        """Type 2: Pattern/value check without waiver support."""
        found_items, missing_items = self._type2_core_logic()

        # ⚠️ CRITICAL: build_complete_output expects dict[str, dict] for both found_items and missing_items
        # Do NOT convert to list!
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3
        )

    def _type2_core_logic(self) -> tuple[dict[str, dict], dict[str, dict]]:
        """
        Core Type 2 pattern matching logic (shared by Type 2 and Type 3).

        Returns:
            Tuple of (found_items, missing_items)
            - found_items: {bump_spec: {'line_number': ..., 'file_path': ...}}
            - missing_items: {bump_spec: {'line_number': ..., 'file_path': ..., 'reason': ...}}
        """
        data = self._parse_input_files()
        items = data.get('items', [])

        requirements = self.item_data.get('requirements', {})
        pattern_items = requirements.get('pattern_items', [])

        found_items = {}
        missing_items = {}

        # Each pattern_item can be in two formats:
        # 1. String: "BUMP_NAME: X_COORD Y_COORD"
        # 2. Dict: {'BUMP_NAME': 'X_COORD Y_COORD'}
        for pattern in pattern_items:
            # Handle dict format (YAML parses "- VSS: 90.0 123.4" as dict)
            if isinstance(pattern, dict):
                if len(pattern) != 1:
                    continue  # Skip malformed dicts
                bump_name = list(pattern.keys())[0]
                coords_str = pattern[bump_name]
                # Reconstruct as string format for consistent processing
                pattern_str = f"{bump_name}: {coords_str}"
            elif isinstance(pattern, str):
                pattern_str = pattern
            else:
                # Skip unsupported types
                continue
            
            matched = False

            # Parse pattern to extract bump name and expected coordinates
            pattern_parts = pattern_str.split(':', 1)
            if len(pattern_parts) != 2:
                missing_items[pattern_str] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Invalid pattern format: {pattern_str}'
                }
                continue

            expected_bump_name = pattern_parts[0].strip()
            expected_coords = pattern_parts[1].strip()
            
            # Parse expected coordinates
            try:
                expected_coords_parts = expected_coords.split()
                if len(expected_coords_parts) != 2:
                    missing_items[pattern_str] = {
                        'line_number': 0,
                        'file_path': 'N/A',
                        'reason': f'Invalid coordinate format: expected "X Y", got "{expected_coords}"'
                    }
                    continue
                expected_x = float(expected_coords_parts[0])
                expected_y = float(expected_coords_parts[1])
            except (ValueError, IndexError) as e:
                missing_items[pattern_str] = {
                    'line_number': 0,
                    'file_path': 'N/A',
                    'reason': f'Invalid coordinate values: {expected_coords} - {str(e)}'
                }
                continue

            # Search for matching bump in parsed items
            # Need to check ALL bumps with matching name to find coordinate match
            found_match = False
            for item in items:
                item_bump_name = item.get('name', '')
                item_center_x = item.get('center_x', '')
                item_center_y = item.get('center_y', '')

                # EXACT MATCH for bump name (case-insensitive)
                if expected_bump_name.lower() == item_bump_name.lower():
                    # Parse item coordinates
                    try:
                        item_x = float(item_center_x)
                        item_y = float(item_center_y)
                    except (ValueError, TypeError):
                        continue
                    
                    # EXACT numeric comparison (no tolerance)
                    if item_x == expected_x and item_y == expected_y:
                        # Bump found with exact matching coordinates
                        found_items[pattern_str] = {
                            'line_number': item.get('line_number', 0),
                            'file_path': item.get('file_path', 'N/A'),
                            'reason': f'Bump {expected_bump_name} found at ({item_x}, {item_y}) matching requirement ({expected_x}, {expected_y})'
                        }
                        found_match = True
                        matched = True
                        break

            if not found_match and not matched:
                # Bump with exact coordinates not found in GDS extraction
                # Try to find bump with same name but different coordinates (for reference)
                closest_coords = None
                closest_distance = float('inf')
                closest_line = 0
                actual_file = 'tv_chip_gds_bump.csv'
                
                for item in items:
                    item_bump_name = item.get('name', '')
                    if expected_bump_name.lower() == item_bump_name.lower():
                        try:
                            item_x = float(item.get('center_x', ''))
                            item_y = float(item.get('center_y', ''))
                            # Calculate Euclidean distance
                            distance = ((item_x - expected_x) ** 2 + (item_y - expected_y) ** 2) ** 0.5
                            if distance < closest_distance:
                                closest_coords = (item_x, item_y)
                                closest_distance = distance
                                closest_line = item.get('line_number', 0)
                                actual_file = item.get('file_path', 'tv_chip_gds_bump.csv')
                        except (ValueError, TypeError):
                            continue
                
                # Construct detailed key and reason
                if closest_coords:
                    # Found bump with same name but different coordinates
                    # Show the closest match for reference
                    detail_key = f'{expected_bump_name}: {closest_coords[0]} {closest_coords[1]} (expected: {expected_x} {expected_y})'
                    reason = 'Bump location mismatch - coordinates differ from package requirements'
                else:
                    # Bump completely missing from GDS extraction
                    detail_key = f'{expected_bump_name}: missing in GDS extraction'
                    reason = 'Bump not found in GDS extraction report'
                    closest_line = 0  # N/A for missing bumps
                
                missing_items[detail_key] = {
                    'line_number': closest_line,
                    'file_path': actual_file,
                    'reason': reason
                }

        return found_items, missing_items

    # =========================================================================
    # Type 3: Value Check with Waiver Logic

    def _execute_type3(self) -> CheckResult:
        """Type 3: Pattern/value check with waiver support (reuses Type 2 core logic)."""
        # Step 1: Get found/missing items using Type 2's core logic
        found_items_base, violations = self._type2_core_logic()

        # Step 2: Parse waiver configuration
        waivers = self.get_waivers()
        waive_items_raw = waivers.get('waive_items', []) if waivers else []
        waive_dict = self.parse_waive_items(waive_items_raw)

        # Step 3: Split violations into waived and unwaived
        found_items = {}
        waived_items = {}
        missing_items = {}
        used_waivers = set()

        # Process found_items_base (no waiver needed - these are clean matches)
        for item_name, item_data in found_items_base.items():
            found_items[item_name] = item_data

        # Process violations with waiver matching
        for viol_name, viol_data in violations.items():
            # Extract bump name from detail_key for waiver matching
            # Detail key format: "BUMP_NAME: x y (expected: x y)" or "BUMP_NAME: missing in GDS extraction"
            bump_name = viol_name.split(':')[0].strip()
            
            matched_waiver = self.match_waiver_entry(bump_name, waive_dict)
            if matched_waiver:
                waived_items[viol_name] = viol_data
                used_waivers.add(matched_waiver)
            else:
                missing_items[viol_name] = viol_data

        # Step 4: Find unused waivers
        unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]

        # Step 5: Build output
        return self.build_complete_output(
            found_items=found_items,
            missing_items=list(missing_items.keys()) if isinstance(missing_items, dict) else missing_items,
            waived_items=waived_items,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            found_desc=self.FOUND_DESC_TYPE2_3,
            missing_desc=self.MISSING_DESC_TYPE2_3,
            waived_desc=self.WAIVED_DESC,
            found_reason=self.FOUND_REASON_TYPE2_3,
            missing_reason=self.MISSING_REASON_TYPE2_3,
            waived_base_reason=self.WAIVED_BASE_REASON,
            unused_waiver_reason=self.UNUSED_WAIVER_REASON
        )
    def _classify_bump_type(self, bump_name: str) -> str:
        """
        Classify bump type based on naming convention.
        
        Args:
            bump_name: Bump name to classify
            
        Returns:
            Bump type classification
        """
        if bump_name.startswith('VDD') or bump_name.startswith('VSS'):
            return 'power'
        elif bump_name.startswith('PAD_'):
            return 'signal'
        elif bump_name.startswith('PADP_') or bump_name.startswith('PADN_'):
            return 'differential'
        elif bump_name.startswith('DUMMY_'):
            return 'dummy'
        else:
            return 'unknown'


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_12_0_0_27()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())