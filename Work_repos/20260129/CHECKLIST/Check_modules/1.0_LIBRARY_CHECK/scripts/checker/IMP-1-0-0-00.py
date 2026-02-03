################################################################################
# Script Name: IMP-1-0-0-00.py
#
# Purpose:
#   Confirm the version of all the libraries used for this project are correct 
#   and match to addendum.
#
#
# Logic:
#   - Parse qor.rpt to extract all library versions
#   - Compare extracted versions with expected versions from addendum
#   - Verify all libraries match required versions
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


class LibraryVersionChecker(BaseChecker):
    """IMP-1-0-0-00: Confirm library versions match addendum."""
    
    def __init__(self):
        super().__init__(
            check_module="1.0_LIBRARY_CHECK",
            item_id="IMP-1-0-0-00",
            item_desc="Confirm the version of all the libraries used for this project are correct and match to addendum."
        )
        # Store version metadata: {version: {line_number, file_path}}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse input files to extract library versions.
        
        Returns:
            List of version strings (deduplicated)
        """
        valid_files, missing_files = self.validate_input_files(raise_on_empty=False)
        
        all_versions = []
        lib_pattern = re.compile(r'^\s*(\S+)\s+(\S+)$')
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            in_tech_lib_section = False
            
            for line_num, line in enumerate(lines, 1):
                if 'Technology libraries:' in line:
                    in_tech_lib_section = True
                    
                    parts = line.split('Technology libraries:')
                    if len(parts) > 1:
                        lib_line = parts[1].strip()
                        match = lib_pattern.match(lib_line)
                        if match:
                            version = match.group(2)
                            all_versions.append(version)
                            if version not in self._metadata:
                                self._metadata[version] = {
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
                    continue
                
                if in_tech_lib_section:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    
                    if any(keyword in line for keyword in [
                        'Operating conditions:', 'Interconnect mode:', 
                        'Area mode:', '============', 'Timing', 'Instance Count'
                    ]):
                        in_tech_lib_section = False
                        continue
                    
                    match = lib_pattern.match(stripped)
                    if match:
                        lib_name = match.group(1)
                        version = match.group(2)
                        if any(pattern in lib_name for pattern in ['tcbn', 'lib', '_', 'cpd', 'bwp']):
                            all_versions.append(version)
                            if version not in self._metadata:
                                self._metadata[version] = {
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
        
        # Deduplicate versions
        unique_versions = list(set(all_versions))
        return sorted(unique_versions) if len(unique_versions) > 1 else unique_versions
    
    def execute_check(self) -> CheckResult:
        """Execute library version check with Type 1/2 logic."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Get configuration
        requirements = self.get_requirements()
        pattern_items = requirements.get('pattern_items', []) if requirements else []
        
        waivers = self.get_waivers()
        waiver_value = waivers.get('value', 'N/A') if waivers else 'N/A'
        waive_items = waivers.get('waive_items', []) if waivers else []
        
        # Detect checker type
        checker_type = self.detect_checker_type()
        
        # Parse input files
        all_versions = self._parse_input_files()
        
        # Execute based on type
        if checker_type == 1:
            return self._execute_type1(all_versions, waiver_value, waive_items)
        else:  # Type 2
            return self._execute_type2(all_versions, pattern_items, waiver_value, waive_items)
    
    def _execute_type1(self, all_versions: List[str], waiver_value: Any, waive_items: List) -> CheckResult:
        """Type 1: Boolean check - just list all versions found."""
        details = []
        
        if not all_versions:
            details.append(DetailItem(
                severity=Severity.FAIL,
                name="",
                line_number=0,
                file_path="N/A",
                reason="No library versions found"
            ))
            return create_check_result(
                value=0,
                is_pass=False,
                has_pattern_items=False,
                has_waiver_value=bool(waive_items),
                details=details,
                item_desc=self.item_desc,
                default_group_desc="No library versions found"
            )
        
        # List all versions as INFO
        for version in all_versions:
            metadata = self._metadata.get(version, {})
            details.append(DetailItem(
                severity=Severity.INFO,
                name=version,
                line_number=metadata.get('line_number', ''),
                file_path=metadata.get('file_path', ''),
                reason="Library version found"
            ))
        
        return create_check_result(
            value=len(all_versions),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc,
            info_groups={
                "INFO01": {
                    "description": "Library versions found",
                    "items": all_versions
                }
            }
        )
    
    def _execute_type2(self, all_versions: List[str], pattern_items: List[str], 
                       waiver_value: Any, waive_items: List) -> CheckResult:
        """Type 2: Value comparison - check against expected versions."""
        details = []
        is_waiver_zero = (waiver_value == 0)
        
        # Classify versions
        matched_versions = [v for v in all_versions if v in pattern_items]
        unmatched_versions = [v for v in all_versions if v not in pattern_items]
        unmatched_patterns = [p for p in pattern_items if p not in all_versions]
        
        if is_waiver_zero:
            # waiver=0: All items become INFO
            for version in all_versions:
                metadata = self._metadata.get(version, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=version,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason=f"Library version found[WAIVED_AS_INFO]"
                ))
            is_pass = True
        else:
            # Normal mode
            for version in matched_versions:
                metadata = self._metadata.get(version, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=version,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Matches expected version"
                ))
            
            for version in unmatched_versions:
                metadata = self._metadata.get(version, {})
                details.append(DetailItem(
                    severity=Severity.FAIL,
                    name=version,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Version doesn't match addendum"
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
            value=len(all_versions),
            is_pass=is_pass,
            has_pattern_items=True,
            has_waiver_value=bool(waive_items),
            details=details,
            item_desc=self.item_desc,
            default_group_desc="Version of all the libraries aren't correct don't match to addendum"
        )


def main():
    """Main entry point for the checker."""
    checker = LibraryVersionChecker()
    checker.run()


if __name__ == '__main__':
    main()
