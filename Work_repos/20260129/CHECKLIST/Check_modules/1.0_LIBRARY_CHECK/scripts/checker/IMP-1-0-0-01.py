################################################################################
# Script Name: IMP-1-0-0-01.py
#
# Purpose:
#   List standard cell libraries used for implementation and signoff.
#
#
# Logic:
#   - Parse qor.rpt to extract standard cell libraries
#   - List all libraries used for implementation and signoff
#   - Categorize libraries by usage type
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


class StandardCellLibraryLister(BaseChecker):
    """IMP-1-0-0-01: List standard cell libraries used for implementation and signoff."""
    
    def __init__(self):
        super().__init__(
            check_module="1.0_LIBRARY_CHECK",
            item_id="IMP-1-0-0-01",
            item_desc="List standard cell libraries used for implementation and signoff."
        )
        # Store library metadata: {lib_name: {line_number, file_path}}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse input files to extract standard cell library names.
        
        Returns:
            List of unique library names
        """
        valid_files, missing_files = self.validate_input_files(raise_on_empty=False)
        
        libraries = []
        lib_pattern = re.compile(r'^\s*(\S+)\s+\S+$')
        
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
                            lib_name = match.group(1)
                            if lib_name not in libraries:
                                libraries.append(lib_name)
                                self._metadata[lib_name] = {
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
                        if any(pattern in lib_name for pattern in ['tcbn', 'lib', '_', 'cpd', 'bwp']):
                            if lib_name not in libraries:
                                libraries.append(lib_name)
                                self._metadata[lib_name] = {
                                    'line_number': line_num,
                                    'file_path': str(file_path)
                                }
        
        return libraries
    
    def execute_check(self) -> CheckResult:
        """Execute standard cell library listing (Type 1 - informational)."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Parse input files
        libraries = self._parse_input_files()
        
        details = []
        
        if not libraries:
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No standard cell libraries found",
                line_number=0,
                file_path="N/A",
                reason="No Technology libraries section detected"
            ))
        else:
            # List each library as INFO
            for lib_name in libraries:
                metadata = self._metadata.get(lib_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=lib_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Standard cell library used for implementation"
                ))
        
        return create_check_result(
            value=len(libraries),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            info_groups={
                "INFO01": {
                    "description": "Standard cell libraries used for implementation",
                    "items": libraries if libraries else ["No standard cell libraries found"]
                }
            }
        )


def main():
    """Main entry point for the checker."""
    checker = StandardCellLibraryLister()
    checker.run()


if __name__ == '__main__':
    main()
