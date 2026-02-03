################################################################################
# Script Name: IMP-5-0-0-12.py
#
# Purpose:
#   Confirm synthesis Quality Of Results (QOR) meets requirements.
#   Extracts TNS, Area, and Power metrics from qor.rpt and compares against thresholds.
#   Supports 4 checking types based on requirements and waivers configuration.
#
# Refactoring to BaseChecker:
#   - Migrated from ValueCheckerBase to unified BaseChecker
#   - Added support for all 4 checking types (Type 1/2/3/4)
#   - Automatic type detection based on requirements.value and waivers.value
#   - Centralized input validation with create_missing_files_error()
#
# Usage:
#   python IMP-5-0-0-12.py [type]
#   type: Optional override (1/2/3/4), default is auto-detect
#
#
# Logic:
#   - Parse qor.rpt to extract QoR metrics (timing/area/power)
#   - Compare actual metrics against requirements
#   - Verify all QoR targets are met
# Author: yyin
# Date:   2025-11-03
# Updated: 2025-11-27 - Migrated to BaseChecker (All 4 Types)
################################################################################

import sys
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Add common modules to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'common'))

from base_checker import BaseChecker, ConfigurationError
from output_formatter import CheckResult, Severity, DetailItem, create_check_result
from parse_qor import (
    extract_timing_from_qor,
    extract_area_from_qor,
    extract_power_from_qor
)


class QorChecker(BaseChecker):
    """
    IMP-5-0-0-12: Confirm synthesis Quality Of Results (QOR) meets requirements?
    
    Extracts TNS, Area, and Power metrics from qor.rpt.
    
    Checking Types:
    - Type 1: requirements=N/A, waivers=N/A/0 → Always PASS (informational only)
    - Type 2: requirements>0, waivers=N/A/0 → FAIL if metrics don't meet thresholds
    - Type 3: requirements>0, waivers>0 → FAIL if unwaived metrics fail
    - Type 4: requirements=N/A, waivers>0 → FAIL if unwaived metrics fail
    
    Metric comparison logic:
    - TNS: actual >= threshold (0) is PASS
    - Area: actual < threshold is PASS (smaller is better)
    - Power: actual < threshold is PASS (smaller is better)
    """
    
    def __init__(self):
        """Initialize the QOR checker."""
        super().__init__(
            check_module="5.0_SYNTHESIS_CHECK",
            item_id="IMP-5-0-0-12",
            item_desc="Confirm synthesis Quality Of Results (QOR) meets requirements (timing, area, power)?"
        )
        # Store metric metadata: {metric_str: {'line': int, 'file': Path, 'details': dict}}
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}
    
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
    
    def _parse_input_files(self, input_files: List[Path]) -> List[str]:
        """
        Extract QOR metrics from qor.rpt.
        
        Returns:
            List of metric strings in format "MetricName:value"
            Example: ["TNS:-5.2", "Area:18000.5", "Power:950.3"]
        """
        if not input_files:
            return []
        
        qor_path = input_files[0]
        metrics = []
        
        try:
            # Extract TNS (Timing)
            timing_info = extract_timing_from_qor(qor_path)
            if timing_info:
                tns_value = self._extract_numeric_value(timing_info.get('tns', '0'))
                if tns_value is not None:
                    metric_str = f"TNS:{tns_value}"
                    metrics.append(metric_str)
                    self.metric_metadata[metric_str] = {
                        'line': timing_info.get('line_number', 0),
                        'file': qor_path,
                        'details': timing_info
                    }
            
            # Extract Area
            area_info = extract_area_from_qor(qor_path)
            if area_info:
                total_area = self._extract_numeric_value(area_info.get('total_area', '0'))
                if total_area is not None:
                    metric_str = f"Area:{total_area}"
                    metrics.append(metric_str)
                    self.metric_metadata[metric_str] = {
                        'line': area_info.get('total_area_line', 0),
                        'file': qor_path,
                        'details': area_info
                    }
            
            # Extract Power
            power_info = extract_power_from_qor(qor_path)
            if power_info:
                total_power = self._extract_numeric_value(power_info.get('total_power', '0'))
                if total_power is not None:
                    metric_str = f"Power:{total_power}"
                    metrics.append(metric_str)
                    self.metric_metadata[metric_str] = {
                        'line': power_info.get('total_power_line', 0),
                        'file': qor_path,
                        'details': power_info
                    }
        
        except Exception as e:
            # Log error but return empty list (will be handled by caller)
            pass
        
        return metrics
    
    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """Extract numeric value from string like "1234.56" or "1.23e-9"."""
        try:
            clean_str = re.sub(r'[^\d.\-e]', '', str(value_str))
            return float(clean_str)
        except (ValueError, AttributeError):
            return None
    
    def _parse_requirement(self, pattern: str) -> Tuple[str, float]:
        """
        Parse requirement pattern like "TNS:0" or "Area:20000".
        
        Returns:
            tuple of (metric_name, threshold_value)
        """
        match = re.match(r'([a-zA-Z]+):\s*([-\d.]+)', pattern.strip())
        if match:
            metric_name = match.group(1).upper()
            threshold = float(match.group(2))
            return (metric_name, threshold)
        return ("", 0.0)
    
    def _compare_metric(self, metric_name: str, actual_value: float, threshold: float) -> bool:
        """
        Compare metric against threshold using metric-specific logic.
        
        Returns:
            True if metric passes, False if it fails
        """
        if metric_name == "TNS":
            return actual_value >= threshold
        elif metric_name in ["AREA", "POWER"]:
            return actual_value < threshold
        else:
            return actual_value == threshold
    
    def _format_metric_reason(self, metric_str: str, is_pass: bool, threshold: Optional[float] = None) -> str:
        """Format detailed reason string for metric."""
        metadata = self.metric_metadata.get(metric_str, {})
        metric_details = metadata.get('details', {})
        
        match = re.match(r'(\w+):\s*([-\d.]+)', metric_str)
        if not match:
            return metric_str
        
        metric_name = match.group(1).upper()
        actual_value = float(match.group(2))
        
        if metric_name == "TNS":
            violating_paths = metric_details.get('violating_paths', 'N/A')
            if is_pass:
                return f"TNS {actual_value} meets requirement (>= {threshold}) with {violating_paths} violating paths"
            else:
                return f"TNS {actual_value} is negative (< {threshold}) with {violating_paths} violating paths"
        
        elif metric_name == "AREA":
            cell_area = metric_details.get('cell_area', 'N/A')
            physical_area = metric_details.get('physical_cell_area', 'N/A')
            if is_pass:
                return f"Area {actual_value} meets requirement (< {threshold}). Cell: {cell_area}, Physical: {physical_area}"
            else:
                return f"Area {actual_value} exceeds requirement (< {threshold}). Cell: {cell_area}, Physical: {physical_area}"
        
        elif metric_name == "POWER":
            power_unit = metric_details.get('total_power_unit', 'nW')
            leakage = metric_details.get('leakage_power', 'N/A')
            dynamic = metric_details.get('dynamic_power', 'N/A')
            if is_pass:
                return f"Power {actual_value} {power_unit} meets requirement (< {threshold}). Leakage: {leakage}, Dynamic: {dynamic}"
            else:
                return f"Power {actual_value} {power_unit} exceeds requirement (< {threshold}). Leakage: {leakage}, Dynamic: {dynamic}"
        
        return metric_str
    
    def _build_waiver_reason_map(self) -> Dict[str, str]:
        """
        Build a mapping from waiver pattern/name to reason.
        
        Returns:
            Dict of {pattern: reason}
        """
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', [])
        
        reason_map = {}
        for item in waive_items:
            if isinstance(item, dict):
                pattern = item.get('name', '')
                reason = item.get('reason', '')
                if pattern:
                    reason_map[pattern] = reason
        
        return reason_map
    
    def _matches_pattern(self, metric_str: str, pattern: str) -> bool:
        """Check if metric string matches a waiver pattern."""
        import fnmatch
        return fnmatch.fnmatch(metric_str, pattern)
    
    def _matches_any_pattern(self, metric_str: str, patterns: List[str]) -> bool:
        """Check if metric string matches any of the waiver patterns."""
        for pattern in patterns:
            if self._matches_pattern(metric_str, pattern):
                return True
        return False
    
    # =========================================================================
    # Type 1: Informational Check (requirements=N/A, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type1(self) -> CheckResult:
        """
        Type 1: Informational check only, always PASS.
        
        Returns:
            CheckResult with is_pass=True, INFO message about QOR metrics
        """
        # Get waiver value for display mode check
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse QOR metrics
        metrics_list = self._parse_input_files(valid_files)
        
        # Build details
        details = []
        if metrics_list:
            for metric_str in metrics_list:
                metadata = self.metric_metadata.get(metric_str, {})
                line_num = metadata.get('line', 0)
                file_path = str(metadata.get('file', Path()).resolve())
                
                reason = f"{metric_str}[WAIVED_AS_INFO]" if is_waiver_zero else f"{metric_str}"
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=metric_str,
                    line_number=line_num,
                    file_path=file_path,
                    reason=reason
                ))
        else:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No QOR metrics extracted from qor.rpt"
            ))
        
        # Add waive_items if waiver=0
        if is_waiver_zero and waive_items:
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
        
        # Always PASS for Type 1
        info_groups = {
            "INFO01": {
                "description": "Check result",
                "items": []
            }
        }
        
        return create_check_result(
            value="N/A",
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 2: Value Check (requirements>0, waivers=N/A/0)
    # =========================================================================
    
    def _execute_type2(self) -> CheckResult:
        """
        Type 2: FAIL if any metric does not meet threshold, PASS if all meet.
        
        Returns:
            CheckResult with is_pass based on metric comparisons
        """
        # Get waiver value for display mode check
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Check if waiver=0 (display mode)
        is_waiver_zero = (waiver_value == 0)
        
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse QOR metrics
        metrics = self._parse_input_files(valid_files)
        
        # Get expected thresholds from pattern_items
        threshold_patterns = self.requirements.pattern_items or []
        
        # Build threshold dict
        thresholds = {}
        for pattern in threshold_patterns:
            metric_name, threshold = self._parse_requirement(pattern)
            if metric_name:
                thresholds[metric_name] = threshold
        
        # Build details
        details = []
        failed_metrics = []
        passed_metrics = []
        
        if not metrics:
            details.append(DetailItem(
                severity=Severity.FAIL,
                name="",
                line_number=0,
                file_path="",
                reason="Failed to extract QOR metrics from qor.rpt"
            ))
            
            return create_check_result(
                value="ERROR",
                is_pass=False,
                has_pattern_items=True,
                has_waiver_value=False,
                details=details,
                error_groups={"ERROR01": {"description": "Execution error", "items": []}},
                item_desc=self.item_desc
            )
        
        # No thresholds configured
        if not thresholds:
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=0,
                file_path="",
                reason="Golden value expected but not provided"
            ))
            
            for metric_str in metrics:
                metadata = self.metric_metadata.get(metric_str, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=metric_str,
                    line_number=metadata.get('line', 0),
                    file_path=str(metadata.get('file', Path()).resolve()),
                    reason=f"{metric_str} measured, but threshold not configured"
                ))
            
            return create_check_result(
                value="0",
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=False,
                details=details,
                warn_groups={"WARN01": {"description": "Configuration Warning", "items": []}},
                info_groups={"INFO01": {"description": "QOR Metrics", "items": metrics}},
                item_desc=self.item_desc
            )
        
        # Compare metrics against thresholds
        for metric_str in metrics:
            match = re.match(r'(\w+):\s*([-\d.]+)', metric_str)
            if not match:
                continue
            
            metric_name = match.group(1).upper()
            actual_value = float(match.group(2))
            
            if metric_name not in thresholds:
                # No threshold for this metric
                passed_metrics.append(metric_str)
                metadata = self.metric_metadata.get(metric_str, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=metric_str,
                    line_number=metadata.get('line', 0),
                    file_path=str(metadata.get('file', Path()).resolve()),
                    reason=f"{metric_str} (no threshold configured)"
                ))
                continue
            
            threshold = thresholds[metric_name]
            is_pass = self._compare_metric(metric_name, actual_value, threshold)
            
            metadata = self.metric_metadata.get(metric_str, {})
            reason = self._format_metric_reason(metric_str, is_pass, threshold)
            
            if is_pass:
                passed_metrics.append(metric_str)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=metric_str,
                    line_number=metadata.get('line', 0),
                    file_path=str(metadata.get('file', Path()).resolve()),
                    reason=reason
                ))
            else:
                failed_metrics.append(metric_str)
                # waiver=0: Convert FAIL to INFO with tag
                if is_waiver_zero:
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=metric_str,
                        line_number=metadata.get('line', 0),
                        file_path=str(metadata.get('file', Path()).resolve()),
                        reason=f"{reason}[WAIVED_AS_INFO]"
                    ))
                else:
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=metric_str,
                        line_number=metadata.get('line', 0),
                        file_path=str(metadata.get('file', Path()).resolve()),
                        reason=reason
                    ))
        
        # Determine pass status
        if is_waiver_zero:
            # waiver=0: Force PASS and convert all to INFO groups
            is_pass = True
            
            # Add waive_items
            for item in waive_items:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=item,
                    line_number=0,
                    file_path="N/A",
                    reason="Waiver item[WAIVED_INFO]"
                ))
            
            all_metrics = passed_metrics + failed_metrics
            info_groups = {
                "INFO01": {
                    "description": "QOR Metrics (waiver=0 display mode)",
                    "items": all_metrics
                }
            }
            error_groups = None
        else:
            # Normal mode
            is_pass = len(failed_metrics) == 0
            
            # Build groups
            if failed_metrics:
                error_groups = {
                    "ERROR01": {
                        "description": "QOR metrics failed to meet requirements",
                        "items": failed_metrics
                    }
                }
                info_groups = None
            else:
                error_groups = None
                info_groups = {
                    "INFO01": {
                        "description": "QOR Metrics",
                        "items": passed_metrics
                    }
                }
        
        return create_check_result(
            value=str(len(failed_metrics)),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            error_groups=error_groups,
            info_groups=info_groups,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 3: Value Check with Waivers (requirements>0, waivers>0)
    # =========================================================================
    
    def _execute_type3(self) -> CheckResult:
        """
        Type 3: Compare metrics with thresholds, allow waivers for specific failing metrics.
        
        Returns:
            CheckResult with FAIL/WAIVED/PASS based on waiver coverage
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse QOR metrics
        metrics = self._parse_input_files(valid_files)
        
        # Get expected thresholds and waivers
        requirements = self.get_requirements()
        waivers = self.get_waivers()
        threshold_patterns = requirements.get('pattern_items', []) or []
        waive_items = waivers.get('waive_items', []) or []
        
        # Extract waiver patterns from waive_items
        waiver_patterns = []
        if waive_items:
            for item in waive_items:
                if isinstance(item, dict):
                    pattern = item.get('name', '')
                    if pattern:
                        waiver_patterns.append(pattern)
                elif isinstance(item, str):
                    waiver_patterns.append(item)
        
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Build threshold dict
        thresholds = {}
        for pattern in threshold_patterns:
            metric_name, threshold = self._parse_requirement(pattern)
            if metric_name:
                thresholds[metric_name] = threshold
        
        if not metrics:
            details = [DetailItem(
                severity=Severity.FAIL,
                name="",
                line_number=0,
                file_path="",
                reason="Failed to extract QOR metrics from qor.rpt"
            )]
            return create_check_result(
                value="ERROR",
                is_pass=False,
                has_pattern_items=True,
                has_waiver_value=True,
                details=details,
                error_groups={"ERROR01": {"description": "Execution error", "items": []}},
                item_desc=self.item_desc
            )
        
        # Separate metrics into passed, failed unwaived, failed waived
        details = []
        passed_metrics = []
        failed_unwaived = []
        failed_waived = []
        unused_waivers = list(waiver_patterns)
        
        for metric_str in metrics:
            match = re.match(r'(\w+):\s*([-\d.]+)', metric_str)
            if not match:
                continue
            
            metric_name = match.group(1).upper()
            actual_value = float(match.group(2))
            
            if metric_name not in thresholds:
                # No threshold configured
                passed_metrics.append(metric_str)
                metadata = self.metric_metadata.get(metric_str, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=metric_str,
                    line_number=metadata.get('line', 0),
                    file_path=str(metadata.get('file', Path()).resolve()),
                    reason=f"{metric_str} (no threshold configured)"
                ))
                continue
            
            threshold = thresholds[metric_name]
            is_pass = self._compare_metric(metric_name, actual_value, threshold)
            metadata = self.metric_metadata.get(metric_str, {})
            
            if is_pass:
                # Metric passes
                passed_metrics.append(metric_str)
                reason = self._format_metric_reason(metric_str, True, threshold)
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=metric_str,
                    line_number=metadata.get('line', 0),
                    file_path=str(metadata.get('file', Path()).resolve()),
                    reason=reason
                ))
            else:
                # Metric fails - check if waived
                is_waived = self._matches_any_pattern(metric_str, waiver_patterns)
                reason = self._format_metric_reason(metric_str, False, threshold)
                
                if is_waived:
                    # Find the matching pattern and its reason
                    matched_pattern = None
                    for pattern in waiver_patterns:
                        if self._matches_pattern(metric_str, pattern):
                            matched_pattern = pattern
                            if pattern in unused_waivers:
                                unused_waivers.remove(pattern)
                            break
                    
                    waiver_reason = waiver_reason_map.get(matched_pattern, "Waived") if matched_pattern else "Waived"
                    failed_waived.append(metric_str)
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=f"{metric_str}",
                        line_number=metadata.get('line', 0),
                        file_path=str(metadata.get('file', Path()).resolve()),
                        reason=f"{reason}[WAIVER]"
                    ))
                else:
                    # Not waived
                    failed_unwaived.append(metric_str)
                    details.append(DetailItem(
                        severity=Severity.FAIL,
                        name=metric_str,
                        line_number=metadata.get('line', 0),
                        file_path=str(metadata.get('file', Path()).resolve()),
                        reason=f"{reason} (not waived)"
                    ))
        
        # Add unused waivers as WARN
        for pattern in unused_waivers:
            reason = waiver_reason_map.get(pattern, "Unused waiver pattern")
            details.append(DetailItem(
                severity=Severity.WARN,
                name=pattern,
                line_number=0,
                file_path="",
                reason=reason
            ))
        
        # Determine pass status
        is_pass = len(failed_unwaived) == 0
        
        # Build groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if failed_unwaived:
            error_groups["ERROR01"] = {
                "description": "QOR metrics failed (not waived)",
                "items": failed_unwaived
            }
        
        if failed_waived:
            info_groups["INFO01"] = {
                "description": "QOR metrics waived and passed",
                "items": [f"{m}" for m in failed_waived]
            }
        
        if passed_metrics and not failed_waived:
            info_groups["INFO01"] = {
                "description": "QOR Metrics",
                "items": passed_metrics
            }
        elif passed_metrics and failed_waived:
            info_groups["INFO02"] = {
                "description": "QOR metrics passed",
                "items": passed_metrics
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": unused_waivers
            }
        
        return create_check_result(
            value=str(len(failed_unwaived)),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=True,
            details=details,
            error_groups=error_groups or None,
            warn_groups=warn_groups or None,
            info_groups=info_groups or None,
            item_desc=self.item_desc
        )
    
    # =========================================================================
    # Type 4: Boolean Check with Waivers (requirements=N/A, waivers>0)
    # =========================================================================
    
    def _execute_type4(self) -> CheckResult:
        """
        Type 4: N/A + PATTERN - Boolean check with waiver logic
        Check if all metrics are covered by waivers (no threshold requirements).
        
        Logic:
        - Metrics matching waiver patterns -> INFO (with [WAIVER] tag)
        - Metrics NOT matching any waiver pattern -> FAIL
        - PASS only if all metrics are waived
        
        Returns:
            CheckResult with FAIL/PASS based on whether all metrics are waived
        """
        # Validate input files
        valid_files, missing_files = self.validate_input_files()
        
        # Handle missing input files
        if missing_files:
            return self.create_missing_files_error(missing_files)
        
        # Parse QOR metrics
        metrics_list = self._parse_input_files(valid_files)
        
        if not metrics_list:
            details = [DetailItem(
                severity=Severity.INFO,
                name="",
                line_number=0,
                file_path="",
                reason="No QOR metrics extracted from qor.rpt"
            )]
            return create_check_result(
                value="N/A",
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=True,
                details=details,
                info_groups={"INFO01": {"description": "Check result", "items": []}},
                item_desc=self.item_desc
            )
        
        # Convert metrics list to dict: {"TNS": value, "Area": value, "Power": value}
        qor_data = {}
        for metric_str in metrics_list:
            # Parse "MetricName:value"
            try:
                metric_name, value_str = metric_str.split(':', 1)
                metric_value = float(value_str)
                qor_data[metric_name] = metric_value
            except (ValueError, AttributeError):
                continue
        
        # Get waiver configuration
        waivers = self.get_waivers()
        waive_items = waivers.get('waive_items', []) or []
        waiver_reason_map = self._build_waiver_reason_map()
        
        # Extract waiver patterns
        waiver_patterns = []
        if waive_items:
            for item in waive_items:
                if isinstance(item, dict):
                    pattern = item.get('name', '')
                    if pattern:
                        waiver_patterns.append(pattern)
                elif isinstance(item, str):
                    waiver_patterns.append(item)
        
        # Classify metrics: waived vs unwaived
        waived_metrics = []
        unwaived_metrics = []
        unused_waivers = list(waiver_patterns)
        
        for metric_str in metrics_list:
            is_waived = False
            matched_pattern = None
            
            # Check if metric matches any waiver pattern
            for pattern in waiver_patterns:
                if self._matches_pattern(metric_str, pattern):
                    is_waived = True
                    matched_pattern = pattern
                    if pattern in unused_waivers:
                        unused_waivers.remove(pattern)
                    break
            
            if is_waived:
                waived_metrics.append((metric_str, matched_pattern))
            else:
                unwaived_metrics.append(metric_str)
        
        # Build details
        details = []
        
        # Unwaived metrics → FAIL
        for metric_str in unwaived_metrics:
            details.append(DetailItem(
                severity=Severity.FAIL,
                name=metric_str,
                line_number=0,
                file_path="",
                reason="Metric not covered by any waiver pattern"
            ))
        
        # Waived metrics → INFO
        for metric_str, matched_pattern in waived_metrics:
            waiver_reason = waiver_reason_map.get(matched_pattern, "Waived")
            details.append(DetailItem(
                severity=Severity.INFO,
                name=metric_str,
                line_number=0,
                file_path="",
                reason=f"{waiver_reason} [WAIVER]"
            ))
        
        # Unused waivers → WARN
        for pattern in unused_waivers:
            reason = waiver_reason_map.get(pattern, "Unused waiver pattern")
            details.append(DetailItem(
                severity=Severity.WARN,
                name=pattern,
                line_number=0,
                file_path="",
                reason=f"{reason} [WAIVER]"
            ))
        
        # Type 4 PASS only if all metrics are waived
        is_pass = len(unwaived_metrics) == 0
        
        # Build groups
        error_groups = {}
        warn_groups = {}
        info_groups = {}
        
        if unwaived_metrics:
            error_groups["ERROR01"] = {
                "description": "Metrics not covered by waivers",
                "items": unwaived_metrics
            }
        
        if waived_metrics:
            info_groups["INFO01"] = {
                "description": "Waived metrics (approved exceptions)",
                "items": [metric_str for metric_str, _ in waived_metrics]
            }
        
        if unused_waivers:
            warn_groups["WARN01"] = {
                "description": "Unused waiver patterns",
                "items": unused_waivers
            }
        
        return create_check_result(
            value="N/A",
            is_pass=is_pass,
            has_pattern_items=False,
            has_waiver_value=True,
            details=details,
            warn_groups=warn_groups or None,
            info_groups=info_groups or None,
            error_groups=error_groups or None,
            item_desc=self.item_desc
        )


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == '__main__':
    checker = QorChecker()
    checker.run()
