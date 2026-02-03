################################################################################
# Script Name: parse_qor.py
#
# Purpose:
#   Parse qor.rpt and extract all Library domain, Technology libraries, Operating conditions, etc.
#
# Usage:
#   python parse_qor.py <path_to_qor.rpt>
#   (Normally invoked by module runner 5.0_SYNTHESIS_CHECK.py)
#
# Author: yyin
# Date:   2025-10-23
################################################################################
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

def parse_qor(qor_path: Path) -> Dict[str, Any]:
    """
    Parse qor.rpt and extract all Library domain, Technology libraries, Operating conditions, etc.
    Returns a dict with all domains and their info.
    """
    if not Path(qor_path).is_file():
        raise FileNotFoundError(f"qor.rpt not found: {qor_path}")
    lines = Path(qor_path).read_text(encoding='utf-8', errors='ignore').splitlines()
    domains = []
    domain = None
    in_domain = False
    tech_libs = []
    domain_name = None
    op_cond = None
    domain_start = 0
    for idx, line in enumerate(lines):
        l = line.strip()
        # Start of a domain
        if l.startswith('Library domain:'):
            if domain:
                # Save previous domain
                domain['technology_libraries'] = tech_libs
                domain['operating_conditions'] = op_cond
                domain['start_line'] = domain_start
                domain['end_line'] = idx
                domains.append(domain)
            domain = {}
            tech_libs = []
            op_cond = None
            domain_name = l.split(':',1)[1].strip()
            domain['domain'] = domain_name
            domain['name'] = domain_name
            domain_start = idx+1
            in_domain = True
            continue
        if in_domain:
            if l.startswith('Technology libraries:'):
                # Collect all following lines until a blank or next section
                for j in range(idx+1, len(lines)):
                    lib_line = lines[j].strip()
                    if not lib_line or lib_line.startswith('Operating conditions:') or lib_line.startswith('Domain index:') or lib_line.startswith('Module:'):
                        break
                    # Library name is first token
                    lib_name = lib_line.split()[0]
                    tech_libs.append(lib_name)
            if l.startswith('Operating conditions:'):
                op_cond = l.split(':',1)[1].strip()
    # Save last domain
    if domain:
        domain['technology_libraries'] = tech_libs
        domain['operating_conditions'] = op_cond
        domain['start_line'] = domain_start
        domain['end_line'] = len(lines)
        domains.append(domain)
    return {'domains': domains}


def extract_timing_from_qor(qor_path: Path) -> Dict[str, Any]:
    """
    Extract timing information (TNS, violating paths) from QoR report.
    
    Returns:
        Dictionary with timing info and line numbers:
        {
            'tns': str,
            'violating_paths': str,
            'line_number': int
        }
    """
    if not Path(qor_path).is_file():
        raise FileNotFoundError(f"qor.rpt not found: {qor_path}")
    
    lines = Path(qor_path).read_text(encoding='utf-8', errors='ignore').splitlines()
    timing_info = {}
    in_timing_section = False
    
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Detect Timing section
        if re.match(r'^Timing\s*$', stripped, re.IGNORECASE):
            in_timing_section = True
            continue
        
        # Exit timing section
        if in_timing_section and (stripped.startswith('Area') or 
                                  stripped.startswith('Power') or 
                                  stripped.startswith('Instance Count')):
            break
        
        # Extract TNS from "Total" line
        if in_timing_section and 'Total' in stripped:
            # Format: "Total    <slack>  <tns>  <violating_paths>"
            match = re.search(r'Total\s+.*\s+([\-\d\.]+)\s+(\d+)\s*$', stripped, re.IGNORECASE)
            if match:
                timing_info['tns'] = match.group(1)
                timing_info['violating_paths'] = match.group(2)
                timing_info['line_number'] = idx
                break
    
    return timing_info


def extract_area_from_qor(qor_path: Path) -> Dict[str, Any]:
    """
    Extract area information from QoR report.
    
    Returns:
        Dictionary with area info and line numbers:
        {
            'total_area': str,
            'total_area_line': int,
            'cell_area': str,
            'cell_area_line': int,
            'physical_cell_area': str,
            'physical_cell_area_line': int,
            ...
        }
    """
    if not Path(qor_path).is_file():
        raise FileNotFoundError(f"qor.rpt not found: {qor_path}")
    
    lines = Path(qor_path).read_text(encoding='utf-8', errors='ignore').splitlines()
    area_info = {}
    in_area_section = False
    
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Detect Area section
        if re.match(r'^Area\s*$', stripped, re.IGNORECASE):
            in_area_section = True
            continue
        
        # Exit area section
        if in_area_section and (stripped.startswith('Power') or stripped.startswith('Number of')):
            break
        
        # Extract area metrics
        if in_area_section:
            if re.match(r'^Cell\s+Area\s+(\S+)', stripped, re.IGNORECASE):
                match = re.match(r'^Cell\s+Area\s+(\S+)', stripped, re.IGNORECASE)
                area_info['cell_area'] = match.group(1)
                area_info['cell_area_line'] = idx
            elif re.match(r'^Physical\s+Cell\s+Area\s+(\S+)', stripped, re.IGNORECASE):
                match = re.match(r'^Physical\s+Cell\s+Area\s+(\S+)', stripped, re.IGNORECASE)
                area_info['physical_cell_area'] = match.group(1)
                area_info['physical_cell_area_line'] = idx
            elif re.match(r'^Total\s+Cell\s+Area\s+\(Cell\+Physical\)\s+(\S+)', stripped, re.IGNORECASE):
                match = re.match(r'^Total\s+Cell\s+Area\s+\(Cell\+Physical\)\s+(\S+)', stripped, re.IGNORECASE)
                area_info['total_cell_area'] = match.group(1)
                area_info['total_cell_area_line'] = idx
            elif re.match(r'^Net\s+Area\s+(\S+)', stripped, re.IGNORECASE):
                match = re.match(r'^Net\s+Area\s+(\S+)', stripped, re.IGNORECASE)
                area_info['net_area'] = match.group(1)
                area_info['net_area_line'] = idx
            elif re.match(r'^Total\s+Area\s+\(Cell\+Physical\+Net\)\s+(\S+)', stripped, re.IGNORECASE):
                match = re.match(r'^Total\s+Area\s+\(Cell\+Physical\+Net\)\s+(\S+)', stripped, re.IGNORECASE)
                area_info['total_area'] = match.group(1)
                area_info['total_area_line'] = idx
    
    return area_info


def extract_power_from_qor(qor_path: Path) -> Dict[str, Any]:
    """
    Extract power information from QoR report.
    
    Returns:
        Dictionary with power info and line numbers:
        {
            'leakage_power': str,
            'leakage_power_unit': str,
            'leakage_power_line': int,
            'dynamic_power': str,
            'dynamic_power_unit': str,
            'dynamic_power_line': int,
            'total_power': str,
            'total_power_unit': str,
            'total_power_line': int
        }
    """
    if not Path(qor_path).is_file():
        raise FileNotFoundError(f"qor.rpt not found: {qor_path}")
    
    lines = Path(qor_path).read_text(encoding='utf-8', errors='ignore').splitlines()
    power_info = {}
    in_power_section = False
    
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        
        # Detect Power section
        if re.match(r'^Power\s*$', stripped, re.IGNORECASE):
            in_power_section = True
            continue
        
        # Exit power section
        if in_power_section and power_info and (stripped.startswith('Number of') or 
                                                 stripped.startswith('Max Fanout') or
                                                 stripped == ''):
            break
        
        # Extract power metrics
        if in_power_section:
            leakage_match = re.search(r'Leakage\s+Power\s+([\d\.]+)\s*(\w+)', stripped, re.IGNORECASE)
            if leakage_match:
                power_info['leakage_power'] = leakage_match.group(1)
                power_info['leakage_power_unit'] = leakage_match.group(2)
                power_info['leakage_power_line'] = idx
            
            dynamic_match = re.search(r'Dynamic\s+Power\s+([\d\.]+)\s*(\w+)', stripped, re.IGNORECASE)
            if dynamic_match:
                power_info['dynamic_power'] = dynamic_match.group(1)
                power_info['dynamic_power_unit'] = dynamic_match.group(2)
                power_info['dynamic_power_line'] = idx
            
            total_match = re.search(r'Total\s+Power\s+([\d\.]+)\s*(\w+)', stripped, re.IGNORECASE)
            if total_match:
                power_info['total_power'] = total_match.group(1)
                power_info['total_power_unit'] = total_match.group(2)
                power_info['total_power_line'] = idx
    
    return power_info
