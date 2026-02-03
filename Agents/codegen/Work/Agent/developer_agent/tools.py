"""
Developer Agent - Tools Implementation
Based on Agent_Development_Spec.md v1.1

Implements log discovery, snippet extraction, and ItemSpec parsing tools.
"""
from typing import List, Dict, Any, Optional
import os
import re
import glob
import gzip


def discover_log_files(
    item_spec_content: str,
    search_root: str,
    max_files: int = 10
) -> Dict[str, List[str]]:
    """
    Discover relevant log files based on ItemSpec description
    
    Args:
        item_spec_content: Content of the ItemSpec document
        search_root: Root directory to search for logs
        max_files: Maximum files per category
        
    Returns:
        Dictionary with categorized file paths:
        {
            "sta_logs": ["/path/to/sta.log", ...],
            "netlist_files": [...],
            "spef_files": [...],
            "other": [...]
        }
    """
    # Extract patterns from ItemSpec
    patterns = extract_file_patterns_from_spec_content(item_spec_content)
    
    results = {}
    for category, pattern_list in patterns.items():
        files = []
        for pattern in pattern_list:
            if os.path.exists(search_root):
                matches = glob.glob(os.path.join(search_root, "**", pattern), recursive=True)
                files.extend(matches[:max_files])
        results[category] = list(set(files))[:max_files]
    
    return results


def extract_file_patterns_from_spec_content(spec_content: str) -> Dict[str, List[str]]:
    """
    Extract file search patterns from ItemSpec content
    
    Note: This function must NOT hardcode any item-specific patterns!
    It dynamically extracts patterns from the spec content.
    
    Args:
        spec_content: Raw ItemSpec content
        
    Returns:
        Dictionary with categorized patterns
    """
    patterns = {
        "sta_logs": [],
        "netlist_files": [],
        "spef_files": [],
        "other": []
    }
    
    # Extract glob patterns from spec (e.g., "*.log", "*.v.gz")
    glob_pattern = re.compile(r'[`"\'](\*\.[a-z]+(?:\.gz)?)[`"\']', re.IGNORECASE)
    matches = glob_pattern.findall(spec_content)
    
    for match in matches:
        match_lower = match.lower()
        if 'log' in match_lower:
            patterns["sta_logs"].append(match)
        elif match.endswith('.v') or match.endswith('.vg') or match.endswith('.v.gz'):
            patterns["netlist_files"].append(match)
        elif 'spef' in match_lower:
            patterns["spef_files"].append(match)
        else:
            patterns["other"].append(match)
    
    # Deduplicate
    for key in patterns:
        patterns[key] = list(set(patterns[key]))
    
    return patterns


def extract_file_patterns_from_spec(parsed_spec: Dict) -> List[str]:
    """
    Extract file patterns from parsed ItemSpec
    
    Args:
        parsed_spec: Parsed ItemSpec dictionary
        
    Returns:
        List of file patterns
    """
    patterns = parsed_spec.get("implementation_hints", {}).get("file_patterns", [])
    if not patterns:
        # Default patterns if none found
        patterns = ["*.log", "*.log.gz", "*.rpt", "*.rpt.gz"]
    return patterns


def extract_keywords_from_spec(parsed_spec: Dict) -> List[str]:
    """
    Extract keywords from parsed ItemSpec for log searching
    
    Args:
        parsed_spec: Parsed ItemSpec dictionary
        
    Returns:
        List of keywords
    """
    keywords = []
    
    # Extract field names from parsing_logic
    for field in parsed_spec.get("parsing_logic", {}).get("target_fields", []):
        name = field.get("name", "")
        if name:
            keywords.append(name)
    
    # Extract keywords from waiver_logic
    keywords.extend(parsed_spec.get("waiver_logic", {}).get("matching_keywords", []))
    
    return [k for k in keywords if k]  # Filter empty values


def extract_log_snippet(
    file_path: str,
    keywords: List[str],
    context_lines: int = 10,
    max_snippet_length: int = 2000
) -> Dict[str, Any]:
    """
    Extract code snippets containing keywords from a log file
    
    Args:
        file_path: Path to the log file
        keywords: Keywords to search for
        context_lines: Number of context lines around match
        max_snippet_length: Maximum length of each snippet
        
    Returns:
        {
            "file_path": "/path/to/file",
            "snippets": [
                {"keyword": "...", "line_number": 42, "content": "..."},
                ...
            ],
            "file_header": "First 50 lines (for version info)"
        }
    """
    try:
        # Handle compressed files
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "snippets": [],
            "file_header": ""
        }
    
    snippets = []
    for keyword in keywords:
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet_content = ''.join(lines[start:end])
                
                if len(snippet_content) > max_snippet_length:
                    snippet_content = snippet_content[:max_snippet_length] + "..."
                
                snippets.append({
                    "keyword": keyword,
                    "line_number": i + 1,
                    "content": snippet_content
                })
                break  # Only first match per keyword
    
    # Extract file header (for version info)
    file_header = ''.join(lines[:50])
    if len(file_header) > max_snippet_length:
        file_header = file_header[:max_snippet_length] + "..."
    
    return {
        "file_path": file_path,
        "snippets": snippets,
        "file_header": file_header
    }


def parse_item_spec(spec_content: str) -> Dict[str, Any]:
    """
    Parse ItemSpec document and extract structured information
    
    Args:
        spec_content: Raw ItemSpec content
        
    Returns:
        {
            "item_id": "IMP-10-0-0-00",
            "parsing_logic": {...},
            "check_logic": {...},
            "waiver_logic": {...},
            "implementation_hints": {...}
        }
    """
    result = {
        "item_id": "",
        "parsing_logic": {},
        "check_logic": {},
        "waiver_logic": {},
        "implementation_hints": {}
    }
    
    # Extract Item ID
    id_match = re.search(r'ItemSpec:\s*(\S+)', spec_content)
    if id_match:
        result["item_id"] = id_match.group(1)
    
    # Also try to extract from title
    if not result["item_id"]:
        title_match = re.search(r'#\s*(\w+-[\d-]+)', spec_content)
        if title_match:
            result["item_id"] = title_match.group(1)
    
    # Extract sections
    sections = re.split(r'\n## \d+\.', spec_content)
    
    for section in sections:
        if 'Parsing Logic' in section or 'parsing logic' in section.lower():
            result["parsing_logic"] = _parse_parsing_section(section)
        elif 'Check Logic' in section or 'check logic' in section.lower():
            result["check_logic"] = _parse_check_section(section)
        elif 'Waiver Logic' in section or 'waiver logic' in section.lower():
            result["waiver_logic"] = _parse_waiver_section(section)
        elif 'Implementation' in section or 'implementation' in section.lower():
            result["implementation_hints"] = _parse_implementation_section(section)
    
    return result


def _parse_parsing_section(section: str) -> Dict:
    """Parse Parsing Logic section"""
    fields = []
    
    # Extract field definitions (e.g., `field_name`: description)
    field_pattern = re.compile(r'`(\w+)`:\s*(.+?)(?=\n|$)')
    for match in field_pattern.finditer(section):
        fields.append({
            "name": match.group(1),
            "description": match.group(2).strip()
        })
    
    # Also try to extract from bullet points
    bullet_pattern = re.compile(r'[-*]\s+`(\w+)`[:\s]+(.+?)(?=\n|$)')
    for match in bullet_pattern.finditer(section):
        field_name = match.group(1)
        if not any(f["name"] == field_name for f in fields):
            fields.append({
                "name": field_name,
                "description": match.group(2).strip()
            })
    
    return {"target_fields": fields}


def _parse_check_section(section: str) -> Dict:
    """Parse Check Logic section"""
    section_lower = section.lower()
    
    # Detect check type
    if 'existence check' in section_lower or 'boolean' in section_lower:
        check_type = "existence"
    elif 'pattern' in section_lower or 'regex' in section_lower:
        check_type = "pattern"
    else:
        check_type = "unknown"
    
    # Extract validation items
    validation_items = []
    item_pattern = re.compile(r'[-*]\s+(.+?)(?=\n[-*]|\n\n|$)', re.DOTALL)
    for match in item_pattern.finditer(section):
        item_text = match.group(1).strip()
        if len(item_text) < 200:  # Filter out overly long matches
            validation_items.append(item_text)
    
    return {
        "type": check_type,
        "validation_items": validation_items[:10]  # Limit to 10
    }


def _parse_waiver_section(section: str) -> Dict:
    """Parse Waiver Logic section"""
    keywords = []
    
    # Extract quoted keywords
    keyword_pattern = re.compile(r'[`"]([^`"]+)[`"]')
    for match in keyword_pattern.finditer(section):
        keyword = match.group(1)
        if len(keyword) < 50:  # Filter overly long matches
            keywords.append(keyword)
    
    # Detect waiver behavior
    global_waiver = "not specified"
    selective_waiver = "not specified"
    
    if 'global' in section.lower():
        if 'skip' in section.lower() or 'bypass' in section.lower():
            global_waiver = "skip all checks"
    
    if 'selective' in section.lower():
        selective_waiver = "waive specific items"
    
    return {
        "matching_keywords": list(set(keywords)),
        "global_waiver_behavior": global_waiver,
        "selective_waiver_behavior": selective_waiver
    }


def _parse_implementation_section(section: str) -> Dict:
    """Parse Implementation Guide section"""
    # Extract file patterns
    patterns = []
    pattern_match = re.compile(r'[`"](\*\.[a-z]+(?:\.gz)?)[`"]', re.IGNORECASE)
    patterns = list(set(pattern_match.findall(section)))
    
    # Extract keywords
    keywords = []
    keyword_pattern = re.compile(r'keyword[s]?[:\s]+[`"]([^`"]+)[`"]', re.IGNORECASE)
    for match in keyword_pattern.finditer(section):
        keywords.append(match.group(1))
    
    # Extract special scenarios
    scenarios = []
    scenario_pattern = re.compile(r'(?:scenario|case|special)[:\s]+(.+?)(?=\n|$)', re.IGNORECASE)
    for match in scenario_pattern.finditer(section):
        scenarios.append(match.group(1).strip())
    
    return {
        "file_patterns": patterns,
        "extraction_keywords": keywords,
        "special_scenarios": scenarios
    }


def discover_files(base_path: str, pattern: str, limit: int = 10) -> Dict[str, List[str]]:
    """
    Discover files matching a pattern
    
    Args:
        base_path: Base directory to search
        pattern: Glob pattern (e.g., "*.log")
        limit: Maximum number of files to return
        
    Returns:
        {"matched_files": [...]}
    """
    if not os.path.exists(base_path):
        return {"matched_files": [], "error": f"Path does not exist: {base_path}"}
    
    matches = glob.glob(os.path.join(base_path, "**", pattern), recursive=True)
    return {"matched_files": matches[:limit]}


def extract_snippet(file_path: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Convenience wrapper for extract_log_snippet
    
    Args:
        file_path: Path to file
        keywords: Keywords to search
        
    Returns:
        Snippet extraction result
    """
    return extract_log_snippet(file_path, keywords)
