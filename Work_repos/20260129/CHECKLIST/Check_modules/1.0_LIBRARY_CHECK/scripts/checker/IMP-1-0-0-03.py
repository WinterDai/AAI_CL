################################################################################
# Script Name: IMP-1-0-0-03.py
#
# Purpose:
#   List all other libraries used for implementation and signoff 
#   (eg: IO/PLL/DCC/BUMP/NoiseGen/ProcessMonitor/etc).
#
#
# Logic:
#   - Parse synthesis log to extract all library usage
#   - Identify non-standard-cell libraries (IO/PLL/DCC/BUMP/etc)
#   - List all other libraries used for implementation
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


class OtherLibraryLister(BaseChecker):
    """IMP-1-0-0-03: List all other libraries (IO/PLL/DCC/BUMP/etc)."""
    
    def __init__(self):
        super().__init__(
            check_module="1.0_LIBRARY_CHECK",
            item_id="IMP-1-0-0-03",
            item_desc="List all other libraries used for implementation and signoff (eg: IO/PLL/DCC/BUMP/NoiseGen/ProcessMonitor/etc)."
        )
        # Store library metadata: {lib_name: {line_number, file_path}}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _parse_input_files(self) -> List[str]:
        """
        Parse input files to extract other (non-standard-cell) libraries.
        
        Returns:
            List of unique library names
        """
        valid_files, missing_files = self.validate_input_files(raise_on_empty=False)
        
        other_libs = []
        
        # Pattern to match "Reading file" lines
        reading_file_pattern = re.compile(r"Reading file\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)
        
        # Standard cell library patterns to exclude
        std_cell_patterns = ['tcbn03e_bwp', '_base_', '_mb_']
        
        # Special library keywords to look for
        special_keywords = ['io', 'pll', 'dcc', 'bump', 'noisegen', 'processmonit', 
                          'monitor', 'analog', 'ams', 'sram', 'rom', 'ram', 
                          'pad', 'esd', 'lvs', 'antenna']
        
        for file_path in valid_files:
            lines = self.read_file(file_path)
            if not lines:
                continue
            
            for line_num, line in enumerate(lines, 1):
                match = reading_file_pattern.search(line)
                if match:
                    lib_file_path = match.group(1)
                    
                    # Extract library identifier from path
                    path_parts = lib_file_path.split('/')
                    for part in path_parts:
                        if part and not part.startswith('.') and len(part) > 5:
                            is_std_cell = any(pattern in part.lower() for pattern in std_cell_patterns)
                            has_special = any(keyword in part.lower() for keyword in special_keywords)
                            
                            if has_special and not is_std_cell:
                                if part not in other_libs:
                                    other_libs.append(part)
                                    self._metadata[part] = {
                                        'line_number': line_num,
                                        'file_path': str(file_path)
                                    }
                                break
        
        return other_libs
    
    def execute_check(self) -> CheckResult:
        """Execute other library listing (Type 1 - informational)."""
        if self.root is None:
            raise RuntimeError("Checker not initialized. Call init_checker() first.")
        
        # Parse input files
        other_libs = self._parse_input_files()
        
        details = []
        
        if not other_libs:
            # Build input files list for the message
            input_files = self.item_data.get('input_files', []) if self.item_data else []
            input_files_str = ", ".join(str(Path(f).name) for f in input_files) if input_files else "N/A"
            
            details.append(DetailItem(
                severity=Severity.INFO,
                name="No other libraries found",
                line_number=0,
                file_path=input_files_str,
                reason=f"No IO/PLL/DCC/BUMP/NoiseGen/ProcessMonitor libraries found"
            ))
        else:
            # List each library as INFO
            for lib_name in other_libs:
                metadata = self._metadata.get(lib_name, {})
                details.append(DetailItem(
                    severity=Severity.INFO,
                    name=lib_name,
                    line_number=metadata.get('line_number', ''),
                    file_path=metadata.get('file_path', ''),
                    reason="Other library used for implementation"
                ))
        
        return create_check_result(
            value=len(other_libs),
            is_pass=True,
            has_pattern_items=False,
            has_waiver_value=False,
            details=details,
            item_desc=self.item_desc,
            info_groups={
                "INFO01": {
                    "description": "Other libraries (IO/PLL/DCC/BUMP/etc)",
                    "items": other_libs if other_libs else ["No other libraries found"]
                }
            }
        )


def main():
    """Main entry point for the checker."""
    checker = OtherLibraryLister()
    checker.run()


if __name__ == '__main__':
    main()
