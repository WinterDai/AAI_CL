################################################################################
# Script Name: IMP-1-0-0-04.py
#
# Purpose:
#   Confirm the versions of analog cells/macros are correct with AMS/Analog team.
#
#
# Logic:
#   - Parse synthesis log to extract analog cell/macro versions
#   - Verify versions match AMS/Analog team specifications
#   - Document version confirmation status
# Author: yyin
# Date:   2025-11-05
# Updated: 2025-12-01 - Migrated to unified BaseChecker architecture
################################################################################

from pathlib import Path
import re
import sys
from typing import List, Dict, Any

# Add common module to path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CHECK_MODULES_DIR = _SCRIPT_DIR.parents[2]  # scripts/checker/ -> scripts/ -> 1.0_LIBRARY_CHECK/
_COMMON_DIR = _CHECK_MODULES_DIR / 'common'
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from base_checker import BaseChecker
from output_formatter import DetailItem, Severity, CheckResult, create_check_result


class AnalogCellVersionChecker(BaseChecker):
    """IMP-1-0-0-04: Confirm analog cell/macro versions."""
    
    def __init__(self):
        super().__init__(
            check_module="1.0_LIBRARY_CHECK",
            item_id="IMP-1-0-0-04",
            item_desc="Confirm the versions of analog cells/macros are correct with AMS/Analog team."
        )
        # Store analog library info: {version_key: {lib_name, version, line_num, file_path}}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _extract_version_from_lib(self, lib_path: Path) -> str:
        """
        Extract VERSION from analog library file.
        
        Look for patterns:
        - /* VERSION            : 101 */
        - /* VERSION HISTORY    : 101 20250325 , Created */
        
        Returns:
            Version string (e.g., "101") or empty string if not found
        """
        if not lib_path.exists():
            return ""
        
        version_pattern = re.compile(r'/\*\s*VERSION\s*(?:HISTORY)?\s*:\s*(\d+)', re.IGNORECASE)
        
        try:
            lines = self.read_file(lib_path)
            if not lines:
                return ""
            
            for line in lines:
                match = version_pattern.search(line)
                if match:
                    return match.group(1)
        except Exception:
            return ""
        
        return ""
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse input files to extract analog library versions.
        
        Returns:
            List of analog library versions (format: "lib_name:version")
        """
        valid_files, missing_files = self.validate_input_files(raise_on_empty=False)
        
        analog_versions = []
        
        # Pattern to match "Reading file" lines
        reading_file_pattern = re.compile(r"Reading file\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)
        
        # Standard cell library patterns to exclude
        std_cell_patterns = ['tcbn03e_bwp', '_base_', '_mb_']
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                match = reading_file_pattern.search(line)
                if match:
                    lib_file_path = match.group(1)
                    
                    # Check if it's a standard cell library (exclude)
                    is_std_cell = any(pattern in lib_file_path.lower() for pattern in std_cell_patterns)
                    if is_std_cell:
                        continue
                    
                    # Check if it's an analog library (*_ana_* pattern)
                    if '_ana_' in lib_file_path.lower():
                        # Extract library name from path
                        path_parts = lib_file_path.split('/')
                        lib_name = None
                        
                        for part in path_parts:
                            if '_ana_' in part.lower():
                                lib_name = part
                                break
                        
                        if not lib_name:
                            lib_name = Path(lib_file_path).stem
                        
                        # Try to read the library file to extract VERSION
                        lib_path = Path(lib_file_path)
                        version = self._extract_version_from_lib(lib_path)
                        
                        if version:
                            version_key = f"{lib_name}:{version}"
                            if version_key not in analog_versions:
                                analog_versions.append(version_key)
                                self._metadata[version_key] = {
                                    'lib_name': lib_name,
                                    'version': version,
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
        
        return analog_versions
    
    def execute_check(self) -> CheckResult:
        """Execute analog version check with Type 1/2 logic."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Get configuration
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        
        # Detect checker type
        checker_type = self.detect_checker_type()
        
        # Parse input files
        analog_versions = self._parse_input_files()
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1(analog_versions)
        else:  # Type 2
            return self._execute_type2(analog_versions, pattern_items, waiver_value)
    
    def _execute_type1(self, analog_versions: List[str]) -> CheckResult:
        """Type 1: Boolean check - just list all analog versions found."""
        details = []
        
        if not analog_versions:
            # Get input file names
            input_files = self.item_data.get('input_files', []) if self.item_data else []
            input_files_str = ", ".join(str(Path(f).name) for f in input_files) if input_files else "N/A"
            
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No analog libraries found",
                line_number=0,
                file_path=input_files_str,
                reason=f"No analog libraries detected"
            ))
        else:
            # List all versions as INFO
            for version_key in analog_versions:
                metadata = self._metadata.get(version_key, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=version_key,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Analog library version found"
                ))
        
        return create_check_result(
            value=len(analog_versions),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            info_groups={
                "INFO01": {
                    "description": "Analog library versions",
                    "items": analog_versions if analog_versions else ["No analog libraries found"]
                }
            }
        )
    
    def _execute_type2(self, analog_versions: List[str], pattern_items: List[str], 
                       waiver_value: Any) -> CheckResult:
        """Type 2: Value comparison - check against expected versions."""
        details = []
        
        if not pattern_items:
            # No pattern_items - show WARN
            details.append(DetailItem(
                severity=Severity.WARN,
                name="",
                line_number=0,
                file_path="N/A",
                reason="Golden value expected but not provided"
            ))
            
            if analog_versions:
                # List found versions as INFO
                for version_key in analog_versions:
                    metadata = self._metadata.get(version_key, {})
                    details.append(DetailItem(
                        severity=Severity.INFO,
                        name=version_key,
                        line_number=metadata.get('line_number', ''),
                        file_path=metadata.get('file_path', ''),
                        reason="Current analog library version"
                    ))
            else:
                # No analog libraries found
                input_files = self.item_data.get('input_files', []) if self.item_data else []
                input_files_str = ", ".join(str(Path(f).name) for f in input_files) if input_files else "N/A"
                
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name="No analog libraries found",
                    line_number=0,
                    file_path=input_files_str,
                    reason=f"No analog libraries detected"
                ))
            
            return create_check_result(
                value=len(analog_versions),
                is_pass=True,
                has_pattern_items=False,
                has_waiver_value=False,
                details=details,
                item_desc=self.item_desc
            )
        
        # Pattern_items defined - validate versions
        is_waiver_zero = (waiver_value == 0)
        
        matched_versions = [v for v in analog_versions if v in pattern_items]
        unmatched_versions = [v for v in analog_versions if v not in pattern_items]
        unmatched_patterns = [p for p in pattern_items if p not in analog_versions]
        
        if is_waiver_zero:
            # waiver=0: All items become INFO
            for version_key in analog_versions:
                metadata = self._metadata.get(version_key, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=version_key,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Analog library version[WAIVED_AS_INFO]"
                ))
            is_pass = True
        else:
            # Normal mode
            for version_key in matched_versions:
                metadata = self._metadata.get(version_key, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=version_key,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Version matches AMS/Analog team requirement"
                ))
            
            for version_key in unmatched_versions:
                metadata = self._metadata.get(version_key, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=version_key,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Version doesn't match AMS/Analog team requirement"
                ))
            
            for pattern in unmatched_patterns:
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=pattern,
                    line_number='',
                    file_path='',
                    reason="Expected version not found"
                ))
            
            is_pass = (len(unmatched_versions) == 0)
        
        return create_check_result(
            value=len(analog_versions),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Analog cell/macro versions don't match AMS/Analog team requirements"
        )


def main():
    """Main entry point for the checker."""
    checker = AnalogCellVersionChecker()
    checker.run()


if __name__ == '__main__':
    main()
