################################################################################
# Script Name: IMP-10-0-0-09.py
#
# Purpose:
#   Confirm no SPEF annotation issue in STA.
#
# Logic:
#   - Parse STA log to locate "report_annotated_parasitics" section
#   - Search for lines starting with "Not annotated real net:" (shell: grep -i "^Not annotated real net:")
#   - If found → FAIL: List all not-annotated real nets
#   - If not found (only "# No not-annotated real net.") → PASS: All nets are annotated
#   - Extract parasitic annotation counts (Res, Cap, XCap) from statistics table
#   - Collect SPEF error/warning messages as supplementary information
#   - Support waiver for not-annotated nets (Type 3/4)
#
# Auto Type Detection:
#   Type 1: requirements.value=N/A, waivers.value=N/A/0 → Boolean check
#   Type 2: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value comparison
#   Type 3: requirements.value>0, pattern_items exists, waivers.value=N/A/0 → Value with waiver logic
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
# Author: yuyin
# Date: 2025-12-10
# Refactored: 2025-12-10 (Using checker_templates - OutputBuilderMixin & WaiverHandlerMixin)
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
from checker_templates.waiver_handler_template import WaiverHandlerMixin
from checker_templates.output_builder_template import OutputBuilderMixin


class Check_10_0_0_09(BaseChecker, WaiverHandlerMixin, OutputBuilderMixin):
    """
    IMP-10-0-0-09: Confirm no SPEF annotation issue in STA.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Informational/Boolean check
    - Type 2: requirements>0, waivers=N/A/0 → Value check without waivers
    - Type 3: requirements>0, waivers>0 → Value check with waiver logic
    - Type 4: requirements=N/A, waivers>0 → Boolean check with waiver logic
    
    Uses WaiverHandlerMixin for waiver processing.
    Uses OutputBuilderMixin for result construction (auto-handles DetailItem creation).
    """
    
    def __init__(self):
        """Initialize the checker."""
        super().__init__(
            check_module="10.0_STA_DCD_CHECK",
            item_id="IMP-10-0-0-09",
            item_desc="Confirm no SPEF annotation issue in STA."
        )
    
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
        Parse STA log file(s) to check for not-annotated real nets.
        
        Shell script equivalent: grep -i "^Not annotated real net:" sta_post_route.log
        - If found → FAIL (list all not-annotated nets)
        - If not found → PASS ("All nets are annotated")
        
        Supports multiple input files - aggregates results from all files.
        
        Returns:
            Dict with:
                - 'not_annotated_nets': List[str] - List of not-annotated real net names
                - 'annotation_counts': Dict - Res/Cap/XCap counts and values from table
                - 'spef_errors': Dict[error_code, metadata] - SPEF errors (supplementary)
                - 'spef_warnings': Dict[warning_code, metadata] - SPEF warnings (supplementary)
                - 'rc_corners': List[str] - RC corner names from all files
                - 'spef_files': List[str] - SPEF file paths from all files
                - 'input_files': List[str] - Paths to input log files
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        if missing_files:
            raise ConfigurationError(
                self.create_missing_files_error(missing_files)
            )
        
        if not valid_files:
            return {
                'not_annotated_nets': [],
                'annotation_counts': {},
                'spef_errors': {},
                'spef_warnings': {},
                'rc_corners': [],
                'spef_files': [],
                'input_files': []
            }
        
        # Aggregated results from all files
        all_not_annotated_nets = []
        all_annotation_counts = {}
        all_errors = {}  # {error_code: {'count': N, 'messages': [...]}}
        all_warnings = {}  # {warning_code: {'count': N, 'messages': [...]}}
        all_rc_corners = []
        all_spef_files = []
        all_views = []  # Extract view names
        
        # Process each input file
        for log_file in valid_files:
            lines = self.read_file(log_file)
            
            # Per-file tracking
            rc_corner = None
            spef_file = None
            view_name = None
            current_view = None  # Track current view for associating with nets
            
            # Patterns
            # Shell script: grep -i "^Not annotated real net:"
            not_annotated_pattern = re.compile(r'^Not annotated real net:\s*(.+)', re.IGNORECASE)
            
            # Extract view name from: #   view: func_rcss_0p675v_125c_pcss_cmax_pcff3_setup
            view_pattern = re.compile(r'^#\s+view:\s+(.+)', re.IGNORECASE)
            
            # Bottom table: | Count | 1275998 | 1252977 | 680338 |
            #               | Value | 54.0873 | 134.1312 | 34.5496 |
            annotation_count_pattern = re.compile(r'\|\s*Count\s+\|\s+([\d]+)\s+\|\s+([\d]+)\s+\|\s+([\d]+)\s+\|')
            annotation_value_pattern = re.compile(r'\|\s*Value\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|')
            
            # Supplementary patterns
            error_pattern = re.compile(r'\*\*ERROR:\s+\(SPEF-(\d+)\):\s+(.+)')
            warn_pattern = re.compile(r'\*\*WARN:\s+\(SPEF-(\d+)\):\s+(.+)')
            rc_corner_pattern = re.compile(r'SPEF files for RC Corner\s+(.+):')
            spef_file_pattern = re.compile(r"Top-level spef file\s+'([^']+)'")
            
            for line_idx, line in enumerate(lines, start=1):
                # Extract view name first (appears before not-annotated nets)
                match = view_pattern.match(line)
                if match:
                    current_view = match.group(1).strip()
                    view_name = current_view  # Keep for metadata collection
                
                # PRIMARY CHECK: "Not annotated real net: <net_name>" (FAIL condition)
                match = not_annotated_pattern.match(line)
                if match:
                    net_name = match.group(1).strip()
                    # Include view info and source for clarity
                    net_with_source = {
                        'name': net_name,
                        'file': str(log_file),
                        'line': line_idx,
                        'view': current_view if current_view else 'Unknown'
                    }
                    all_not_annotated_nets.append(net_with_source)
                
                # Extract annotation counts (Res, Cap, XCap) - aggregate across files
                match = annotation_count_pattern.search(line)
                if match:
                    # Sum up counts from multiple files
                    all_annotation_counts['res_count'] = all_annotation_counts.get('res_count', 0) + int(match.group(1))
                    all_annotation_counts['cap_count'] = all_annotation_counts.get('cap_count', 0) + int(match.group(2))
                    all_annotation_counts['xcap_count'] = all_annotation_counts.get('xcap_count', 0) + int(match.group(3))
                
                # Extract annotation values - keep latest (or sum if needed)
                match = annotation_value_pattern.search(line)
                if match:
                    all_annotation_counts['res_value'] = all_annotation_counts.get('res_value', 0.0) + float(match.group(1))
                    all_annotation_counts['cap_value'] = all_annotation_counts.get('cap_value', 0.0) + float(match.group(2))
                    all_annotation_counts['xcap_value'] = all_annotation_counts.get('xcap_value', 0.0) + float(match.group(3))
                
                # Metadata - RC corner
                match = rc_corner_pattern.search(line)
                if match:
                    rc_corner = match.group(1)
                
                # Metadata - SPEF file
                match = spef_file_pattern.search(line)
                if match:
                    spef_file = match.group(1)
                
                # Supplementary: SPEF errors - aggregate
                match = error_pattern.search(line)
                if match:
                    code = f"SPEF-{match.group(1)}"
                    message = match.group(2).strip()
                    if code not in all_errors:
                        all_errors[code] = {'count': 0, 'messages': []}
                    all_errors[code]['count'] += 1
                    if len(all_errors[code]['messages']) < 3:
                        all_errors[code]['messages'].append(f"{message} ({log_file.name})")
                
                # Supplementary: SPEF warnings - aggregate
                match = warn_pattern.search(line)
                if match:
                    code = f"SPEF-{match.group(1)}"
                    message = match.group(2).strip()
                    if code not in all_warnings:
                        all_warnings[code] = {'count': 0, 'messages': []}
                    all_warnings[code]['count'] += 1
                    if len(all_warnings[code]['messages']) < 3:
                        all_warnings[code]['messages'].append(f"{message} ({log_file.name})")
            
            # Collect metadata from this file
            if rc_corner:
                all_rc_corners.append(rc_corner)
            if spef_file:
                all_spef_files.append(spef_file)
            if view_name:
                all_views.append(view_name)
        
        return {
            'not_annotated_nets': all_not_annotated_nets,
            'annotation_counts': all_annotation_counts,
            'spef_errors': all_errors,
            'spef_warnings': all_warnings,
            'rc_corners': all_rc_corners,
            'spef_files': all_spef_files,
            'views': all_views,
            'input_files': [str(f) for f in valid_files]
        }
    
    # =========================================================================
    # Type 1: Informational/Boolean Check
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check - report annotation parasitics status.
        
        Shell script logic:
        - If "Not annotated real net:" found → FAIL: List all not-annotated nets
        - If not found → PASS: "All nets are annotated"
        
        Supports waivers.value=0 automatic FAIL→INFO conversion via build_complete_output().
        
        Returns:
            CheckResult with PASS if all nets annotated, FAIL if any not-annotated
        """
        # Parse input
        data = self._parse_input_files()
        
        not_annotated_nets = data['not_annotated_nets']
        views = data['views']
        errors = data['spef_errors']
        warnings = data['spef_warnings']
        
        # Get views that have FAIL
        failed_views = set()
        for net_info in not_annotated_nets:
            failed_views.add(net_info.get('view', 'Unknown'))
        
        # Build found_items (only views without FAIL)
        found_items = {}
        for view in views:
            if view not in failed_views:
                found_items[view] = {
                    'line_number': 0,
                    'file_path': data['input_files'][0] if data['input_files'] else ''
                }
        
        # Build missing_items (not-annotated nets) - just a simple list
        missing_items = []
        if not_annotated_nets:
            for net_info in not_annotated_nets:
                net_name = net_info['name']
                view_name = net_info.get('view', 'Unknown')
                # Display format: net_name (view: xxx)
                display_name = f"{net_name} (view: {view_name})"
                missing_items.append(display_name)
        
        # Add SPEF errors if any
        if errors:
            for code, info in errors.items():
                error_name = f"{code}: {info['count']} error(s)"
                missing_items.append(error_name)
        
        # Name extractor
        def extract_info(name, metadata):
            if isinstance(metadata, dict):
                if 'message' in metadata:
                    return metadata.get('message', name)
            return name
        
        # Use build_complete_output for automatic waiver=0 handling
        # Type 1 uses has_pattern_items=False, has_waiver_value=False
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=None,  # Type 1 has no waiver logic (unless waiver=0)
            unused_waivers=None,
            waive_dict={},
            value="N/A",
            has_pattern_items=False,
            has_waiver_value=False,
            default_file=data['input_files'][0] if data['input_files'] else '',
            name_extractor=extract_info,
            found_reason="All nets are annotated",
            missing_reason="Not-annotated real net detected",
            waived_base_reason="Not-annotated real net detected",
            unused_waiver_reason="Waiver unused (net is annotated)",
            found_desc="No SPEF annotation issue in STA",
            missing_desc="SPEF annotation issues found in STA",
            waived_desc="[WAIVED_INFO]: Waived SPEF annotation issues",
            unused_desc="Unused waivers"
        )
    
    # =========================================================================
    # Type 2: Value Check (No Waivers)
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: Value check - verify specific views from pattern_items have no not-annotated nets.
        Similar to Type 1 but checks specific views from pattern_items.
        
        Supports waivers.value=0 automatic FAIL→INFO conversion via build_complete_output().
        
        Returns:
            CheckResult comparing not-annotated net counts per view vs requirements.value
        """
        # Parse input
        data = self._parse_input_files()
        not_annotated_nets = data['not_annotated_nets']
        views = data['views']
        
        # Get requirements
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', [])
        # Note: requirements.value indicates number of views to check (len of pattern_items)
        # NOT the allowed number of not-annotated nets per view!
        # Any not-annotated net in any view is a FAIL condition
        
        # Check pattern_items or all views
        views_to_check = pattern_items if pattern_items else views
        
        # Build view -> not-annotated nets mapping
        view_nets_map = {}
        for view in views_to_check:
            view_nets_map[view] = []
        
        for net_info in not_annotated_nets:
            view_name = net_info.get('view', 'Unknown')
            if view_name in views_to_check:
                view_nets_map[view_name].append(net_info)
        
        # Build found_items (views with no not-annotated nets)
        # Build missing_items as simple list
        found_items = {}
        missing_items = []
        
        for view in views_to_check:
            nets = view_nets_map.get(view, [])
            net_count = len(nets)
            
            # PASS only when net_count == 0 (no not-annotated nets)
            if net_count == 0:
                # PASS view
                found_items[view] = {
                    'line_number': 0,
                    'file_path': data['input_files'][0] if data['input_files'] else ''
                }
            else:
                # FAIL view - add each not-annotated net as missing item
                for net_info in nets:
                    net_name = net_info['name']
                    display_name = f"[{net_name}] (view: {view})"
                    missing_items.append(display_name)
        
        # Name extractor
        def extract_info(name, metadata):
            if isinstance(metadata, dict):
                if 'message' in metadata:
                    return metadata.get('message', name)
            return name
        
        # Use build_complete_output for automatic waiver=0 handling
        # Type 2 uses has_pattern_items=True, has_waiver_value=False
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=None,  # Type 2 has no waiver logic (unless waiver=0)
            unused_waivers=None,
            waive_dict={},
            value=len(found_items),
            has_pattern_items=True,
            has_waiver_value=False,
            default_file=data['input_files'][0] if data['input_files'] else '',
            name_extractor=extract_info,
            found_reason="All nets are annotated",
            missing_reason="Not-annotated real net detected",
            waived_base_reason="Not-annotated real net detected",
            unused_waiver_reason="Waiver unused (net is annotated)",
            found_desc="No SPEF annotation issue in STA",
            missing_desc="SPEF annotation issues found in STA",
            waived_desc="[WAIVED_INFO]: Waived SPEF annotation issues",
            unused_desc="Unused waivers"
        )
    
    # =========================================================================
    # Type 3: Value Check with Waiver Logic
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Value check with waiver support - verify specific views from pattern_items.
        Similar to Type 2 but with waiver support for not-annotated nets.
        
        Returns:
            CheckResult with waiver logic - specific not-annotated nets can be waived
        """
        # Parse input
        data = self._parse_input_files()
        not_annotated_nets = data['not_annotated_nets']
        views = data['views']
        
        # Get requirements and waivers
        requirements = self.get_requirements()
        waiver_config = self.get_waiver_config()
        pattern_items = requirements.get('pattern_items', [])
        # Note: requirements.value indicates number of views to check (len of pattern_items)
        # NOT the allowed number of not-annotated nets per view!
        # Any unwaived not-annotated net in any view is a FAIL condition
        waive_items_raw = waiver_config.get('waive_items', [])
        
        # Parse waivers
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Check pattern_items or all views
        views_to_check = pattern_items if pattern_items else views
        
        # Build view -> not-annotated nets mapping
        view_nets_map = {}
        for view in views_to_check:
            view_nets_map[view] = []
        
        for net_info in not_annotated_nets:
            view_name = net_info.get('view', 'Unknown')
            if view_name in views_to_check:
                view_nets_map[view_name].append(net_info)
        
        # Collect all not-annotated nets for waiver classification
        # Support both view-level and net-level waivers
        all_net_display_names = []  # For classification
        net_metadata_map = {}  # display_name -> net_info
        
        for view in views_to_check:
            nets = view_nets_map.get(view, [])
            for net_info in nets:
                net_name = net_info['name']
                view_name = net_info.get('view', 'Unknown')
                # Create display name for matching
                display_name = f"{net_name} (view: {view_name})"
                all_net_display_names.append(display_name)
                net_metadata_map[display_name] = net_info
        
        # Extended waive_dict to support view-level waivers
        extended_waive_dict = dict(waive_dict)
        for waive_item in waive_dict.keys():
            # If waiver is a view name, waive all nets in that view
            if waive_item in views_to_check:
                # Add all nets in this view to waive_dict
                for display_name in all_net_display_names:
                    if f"(view: {waive_item})" in display_name:
                        extended_waive_dict[display_name] = f"View {waive_item} is waived"
        
        # Classify by waiver
        waived_nets, unwaived_nets = self.classify_items_by_waiver(
            all_items=all_net_display_names,
            waive_dict=extended_waive_dict
        )
        
        # Find unused waivers (check both original and extended)
        unused_waivers = []
        for waive_item in waive_dict.keys():
            # Check if it's a view-level waiver
            if waive_item in views_to_check:
                # Check if any nets in this view were found
                view_has_nets = any(f"(view: {waive_item})" in dn for dn in all_net_display_names)
                if not view_has_nets:
                    unused_waivers.append(waive_item)
            else:
                # Net-level waiver - check if it was used
                if waive_item not in all_net_display_names:
                    unused_waivers.append(waive_item)
        
        # Build found_items (PASS views), waived_items, missing_items
        found_items = {}
        waived_items_list = []
        missing_items = []
        missing_items_dict = {}
        waived_items_dict = {}
        
        for view in views_to_check:
            nets = view_nets_map.get(view, [])
            
            # Count unwaived nets in this view
            unwaived_in_view = [dn for dn in unwaived_nets if f"(view: {view})" in dn]
            unwaived_count = len(unwaived_in_view)
            
            # PASS only when unwaived_count == 0 (no unwaived not-annotated nets)
            if unwaived_count == 0:
                # PASS view (all nets either annotated or waived)
                if len(nets) == 0:
                    found_items[view] = {
                        'message': f'All nets are annotated (view: {view})',
                        'line_number': 0,
                        'file_path': data['input_files'][0] if data['input_files'] else ''
                    }
        
        # Add waived nets
        for display_name in waived_nets:
            net_info = net_metadata_map[display_name]
            net_name = net_info['name']
            view_name = net_info.get('view', 'Unknown')
            final_display = f"[{net_name}] (view: {view_name})"
            waived_items_list.append(final_display)
            waived_items_dict[final_display] = {
                'line_number': net_info['line'],
                'file_path': net_info['file']
            }
        
        # Add unwaived nets (FAIL)
        for display_name in unwaived_nets:
            net_info = net_metadata_map[display_name]
            net_name = net_info['name']
            view_name = net_info.get('view', 'Unknown')
            final_display = f"[{net_name}] (view: {view_name})"
            missing_items.append(final_display)
            missing_items_dict[final_display] = {
                'line_number': net_info['line'],
                'file_path': net_info['file']
            }
        
        # Name extractor
        def extract_info(name, metadata):
            if isinstance(metadata, dict):
                if 'message' in metadata:
                    return metadata.get('message', name)
            return name
        
        # Build details using build_complete_output with waiver support
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items_list,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            value=len(found_items),
            has_pattern_items=True,
            has_waiver_value=True,
            default_file=data['input_files'][0] if data['input_files'] else '',
            name_extractor=extract_info,
            found_reason="All nets are annotated",
            missing_reason="Not-annotated real net detected (not waived)",
            waived_base_reason="Not-annotated real net detected",
            unused_waiver_reason="Waiver unused (net is annotated)",
            found_desc="No SPEF annotation issue in STA",
            missing_desc="SPEF annotation issues found in STA",
            waived_desc="Waived SPEF annotation issues",
            unused_desc="Unused waivers"
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waiver Logic
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: Boolean check with waiver support - global check across all views.
        Similar to Type 1 but with waiver support for not-annotated nets.
        
        Returns:
            CheckResult with waiver logic applied
        """
        # Parse input
        data = self._parse_input_files()
        not_annotated_nets = data['not_annotated_nets']
        views = data['views']
        
        # Get waivers
        waiver_config = self.get_waiver_config()
        waive_items_raw = waiver_config.get('waive_items', [])
        
        # Parse waivers
        waive_dict = self.parse_waive_items(waive_items_raw)
        
        # Build net display name list and metadata map
        # Support both view-level and net-level waivers
        all_net_display_names = []
        net_metadata_map = {}  # display_name -> net_info
        
        for net_info in not_annotated_nets:
            net_name = net_info['name']
            view_name = net_info.get('view', 'Unknown')
            display_name = f"{net_name} (view: {view_name})"
            all_net_display_names.append(display_name)
            net_metadata_map[display_name] = net_info
        
        # Extended waive_dict to support view-level waivers
        extended_waive_dict = dict(waive_dict)
        for waive_item in waive_dict.keys():
            # If waiver is a view name, waive all nets in that view
            if waive_item in views:
                # Add all nets in this view to waive_dict
                for display_name in all_net_display_names:
                    if f"(view: {waive_item})" in display_name:
                        extended_waive_dict[display_name] = f"View {waive_item} is waived"
        
        # Classify by waiver
        waived_nets, unwaived_nets = self.classify_items_by_waiver(
            all_items=all_net_display_names,
            waive_dict=extended_waive_dict
        )
        
        # Find unused waivers (check both original and extended)
        unused_waivers = []
        for waive_item in waive_dict.keys():
            # Check if it's a view-level waiver
            if waive_item in views:
                # Check if any nets in this view were found
                view_has_nets = any(f"(view: {waive_item})" in dn for dn in all_net_display_names)
                if not view_has_nets:
                    unused_waivers.append(waive_item)
            else:
                # Net-level waiver - check if it was used
                if waive_item not in all_net_display_names:
                    unused_waivers.append(waive_item)
        
        # Get views that have unwaived FAIL
        failed_views = set()
        for display_name in unwaived_nets:
            net_info = net_metadata_map[display_name]
            failed_views.add(net_info.get('view', 'Unknown'))
        
        # Build found_items (only views without unwaived FAIL)
        found_items = {}
        for view in views:
            if view not in failed_views:
                found_items[view] = {
                    'message': f'All nets are annotated (view: {view})',
                    'line_number': 0,
                    'file_path': data['input_files'][0] if data['input_files'] else ''
                }
        
        # Build waived_items, missing_items
        waived_items_list = []
        missing_items = []
        
        # Add waived nets
        for display_name in waived_nets:
            net_info = net_metadata_map[display_name]
            net_name = net_info['name']
            view_name = net_info.get('view', 'Unknown')
            final_display = f"{net_name} (view: {view_name})"
            waived_items_list.append(final_display)
        
        # Add unwaived nets (FAIL)
        for display_name in unwaived_nets:
            net_info = net_metadata_map[display_name]
            net_name = net_info['name']
            view_name = net_info.get('view', 'Unknown')
            final_display = f"{net_name} (view: {view_name})"
            missing_items.append(final_display)
        
        # Name extractor
        def extract_info(name, metadata):
            if isinstance(metadata, dict):
                if 'message' in metadata:
                    return metadata.get('message', name)
            return name
        
        return self.build_complete_output(
            found_items=found_items,
            missing_items=missing_items,
            waived_items=waived_items_list,
            unused_waivers=unused_waivers,
            waive_dict=waive_dict,
            value="N/A",
            has_pattern_items=False,
            has_waiver_value=True,
            default_file=data['input_files'][0] if data['input_files'] else '',
            name_extractor=extract_info,
            found_reason="All nets are annotated",
            missing_reason="Not-annotated real net detected (not waived)",
            waived_base_reason="Not-annotated real net detected",
            unused_waiver_reason="Waiver unused (net is annotated)",
            found_desc="No SPEF annotation issue in STA",
            missing_desc="SPEF annotation issues found in STA",
            waived_desc="Waived SPEF annotation issues",
            unused_desc="Unused waivers"
        )


# =========================================================================
# Entry Point
# =========================================================================

def main():
    """Main entry point."""
    checker = Check_10_0_0_09()
    checker.init_checker(Path(__file__))
    result = checker.execute_check()
    checker.write_output(result)
    return 0 if result.is_pass else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
