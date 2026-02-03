################################################################################
# Script Name: write_summary_yaml.py
#
# Purpose:
#   Parse individual item .rpt files into module summary YAML consolidating Fail/Warn/Info.
#   Provide normalized structure consumed by excel_generator and higher-level aggregation.
#
# Usage:
#   python write_summary_yaml.py -root <ROOT> -module 5.0_SYNTHESIS_CHECK -out <OUTPUT_PATH>
#   (Normally invoked by 5.0_SYNTHESIS_CHECK.py)
#
# Author: yyin
# Date:   2025-10-23
################################################################################
import sys
import subprocess
import argparse
import yaml
from yaml import SafeDumper
import shutil
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import datetime

def parse_report(report_path: Path, item_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse a report file of the form:
      ITEM_ID:Description text ...
      [INFO]:Summary message (optional, for Type 4 checkers)
      Fail Occurrence: N
      1: Fail: Cell CELLNAME. In line L, /path/file : Uses prohibited cell *XXX*
    
    Special handling:
    1. [ERROR]: messages (generic errors) → create failure with N/A details
    2. [INFO]: summary message (Type 4 checkers) → stored as info_message field
    3. Pass Occurrence: + Library Used: list → create infos with library details
    
    NEW OPTIMIZATION:
    4. Try to get data from memory cache first (fastest!)
    5. Otherwise, fallback to regex parsing report file (backward compatible)
    
    Args:
        report_path: Path to the report file
        item_id: Optional item ID to lookup in memory cache
    """
    # NEW: Try to load from cache (memory or file based on configuration)
    if item_id:
        try:
            from base_checker import BaseChecker
            
            # Try 1: Memory cache (fastest, works in same process)
            cached_result = BaseChecker.get_cached_result(item_id)
            if cached_result:
                #print(f"[DEBUG] Cache HIT (memory) for {item_id}")
                # Get data in parse_report() compatible format
                data = cached_result.get_summary_data()
                data["id"] = item_id
                # Description is included in summary_data from CheckResult
                return data
            
            # Try 2: File cache from outputs/.cache/ directory (cross-process, always try)
            # Construct cache path: Check_modules/{module}/outputs/.cache/{item_id}.pkl
            try:
                module_dir = report_path.parent.parent  # reports/ -> module/
                cache_dir = module_dir / 'outputs' / '.cache'
                cache_file = cache_dir / f'{item_id}.pkl'
                
                if cache_file.exists():
                    import pickle
                    try:
                        with open(cache_file, 'rb') as f:
                            cached_result = pickle.load(f)
                        
                        # Cache hit - silently use cached data
                        # Get data in parse_report() compatible format
                        data = cached_result.get_summary_data()
                        data["id"] = item_id
                        # Description is included in summary_data from CheckResult
                        return data
                    except Exception as e:
                        print(f"[DEBUG] File cache read failed: {e}")
            except Exception:
                pass  # Path construction failed, continue to report parsing
                
        except Exception:
            print(f"[DEBUG] Cache MISS for {item_id} - will parse report file")
            pass
    
    # FALLBACK: Parse report file using regex (original logic)
    data: Dict[str, Any] = {}
    if not report_path.is_file():
        return data
    try:
        lines = [l.rstrip("\n") for l in report_path.open("r", encoding="utf-8", errors="ignore")]
        if not lines:
            return data
        # First line format: PASS/FAIL:ITEM_ID:Description
        # Extract ITEM_ID and Description (skip PASS/FAIL status)
        m = re.match(r'^[^:]+:([^:]+):(.*)$', lines[0])
        if m:
            data["id"] = m.group(1).strip()
            data["description"] = m.group(2).strip()
        
        # Check for [INFO]: summary message pattern (Type 4 checkers, line 2)
        # Example: "[INFO]:Empty Modules are none or explained in C:\path\to\file.log"
        # This should be added to infos list, not as a separate field
        info_summary_re = re.compile(r'^\[INFO\]:\s*(.+)$')
        infos = []
        if len(lines) > 1:
            info_summary_match = info_summary_re.match(lines[1])
            if info_summary_match:
                # Add as first info item
                infos.append({
                    "index": 1,
                    "detail": info_summary_match.group(1).strip(),
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": "Summary"
                })
        
        # Check for [ERROR]: pattern (generic error, no structured failures)
        error_re = re.compile(r'^\[ERROR\]:\s*(.+)$')
        for ln in lines[1:]:
            em = error_re.match(ln)
            if em:
                error_msg = em.group(1).strip()
                # Create a single failure entry with N/A values
                data["occurrence"] = 1
                data["failures"] = [{
                    "index": 1,
                    "fail_status": "Fail",
                    "detail": "N/A",
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": error_msg
                }]
                return data
        
        # Occurrence lines (may be second line) - capture Fail and Warn occurrences
        if len(lines) > 1:
            m_fail_occ = re.match(r'^Fail\s+Occurrence:\s*(\d+)', lines[1], re.IGNORECASE)
            if m_fail_occ:
                data["occurrence"] = int(m_fail_occ.group(1))
            m_warn_occ = re.match(r'^Warn\s+Occurrence:\s*(\d+)', lines[1], re.IGNORECASE)
            if m_warn_occ:
                # store separately as warning_occurrence for consistency
                data["warning_occurrence"] = int(m_warn_occ.group(1))
            # Check for Pass Occurrence (libraries used info)
            m_pass_occ = re.match(r'^Pass\s+Occurrence:\s*(\d+)', lines[1], re.IGNORECASE)
            if m_pass_occ:
                data["info_occurrence"] = int(m_pass_occ.group(1))
        
        failures = []
        # Simplified pattern: matches "N: Fail: detail. In line L, path : reason"
        # Captures: (1) index, (2) Pass/Fail, (3) detail, (4) line, (5) file, (6) reason
        failure_re = re.compile(
            r'^(\d+):\s*(Pass|Fail):\s*(.+?)\.?\s+In line\s+(\d+|Unknown),\s*(\S.+?)\s*:\s*(.*)$'
        )
        # Ultra simplified fail pattern: matches "N: Fail: reason" (no detail, no file/line)
        fail_ultra_simple_re = re.compile(r'^(\d+):\s*Fail:\s*(.*)$')
        
        # Note: infos list is already initialized above (for [INFO]: summary)
        info_occurrence: Optional[int] = None
        info_occ_re = re.compile(r'^Info\s+Occurrence:\s*(\d+)', re.IGNORECASE)
        # Simplified info pattern: matches "N: Info: detail. In line L, path : reason"
        info_re = re.compile(r'^(\d+):\s*Info:\s*(.+?)\.?\s+In line\s+(\d+|Unknown|N/A),\s*(\S.+?)\s*:\s*(.*)$')
        # Even more simplified info pattern: matches "N: Info: detail. : reason" (no file/line info)
        info_simple_re = re.compile(r'^(\d+):\s*Info:\s*(.+?)\.\s*:\s*(.*)$')
        # Ultra simplified: matches "N: Info: reason" (no detail, no file/line)
        info_ultra_simple_re = re.compile(r'^(\d+):\s*Info:\s*(.*)$')
        
        warnings = []
        warn_occurrence: Optional[int] = None
        warn_occ_re = re.compile(r'^Warn\s+Occurrence:\s*(\d+)', re.IGNORECASE)
        # Simplified warning pattern: matches "N: Warn: detail. In line L, path : reason"
        warn_re = re.compile(r'^(\d+):\s*Warn:\s*(.+?)\.?\s+In line\s+(\d+|Unknown|N/A),\s*(\S.+?)\s*:\s*(.*)$')
        # Type 3 warning pattern: matches "N: Warn: detail : reason" (colon-separated, no file/line)
        # Example: "1: Warn: CELL_NAME_PATTERN : Waived items are not used[WAIVER]"
        warn_name_reason_re = re.compile(r'^(\d+):\s*Warn:\s*([^:]+?)\s*:\s*(.+)$')
        # Ultra simplified warn pattern: matches "N: Warn: reason" (no detail, no file/line)
        warn_ultra_simple_re = re.compile(r'^(\d+):\s*Warn:\s*(.*)$')
        # Alternate warning pattern for reports using 'In file' syntax without line number
        # Example: 1: Warn: C:\path\to\log.log. In file C:\path\to\log.log: message text
        warn_file_re = re.compile(r'^(\d+):\s*Warn:\s*(.+?)\.?\s+In file\s+(\S.+?)\s*:\s*(.*)$')
        
        # Pattern for Pass case: any list items after "Pass Occurrence: N"
        # This is generic and works for any checker output format
        in_pass_list = False
        pass_list_re = re.compile(r'^\s*-\s+(.+)$')
        
        # NEW: Tag format patterns for Type 1 Boolean checkers
        # Matches: [INFO] message text
        info_tag_re = re.compile(r'^\[INFO\]\s+(.+)$')
        # Matches: [WAIVE_INFO]:message text (note the colon)
        waive_tag_re = re.compile(r'^\[WAIVE_INFO\]:(.+)$')
        
        # Check if report uses tag format (starting from line 2)
        # If line 2 starts with [INFO] or [WAIVE_INFO], use tag parsing mode
        use_tag_format = False
        if len(lines) > 1:
            second_line = lines[1].strip()
            if second_line.startswith('[INFO]') or second_line.startswith('[WAIVE_INFO]'):
                use_tag_format = True
        
        # Start parsing from line 2 (index 1) - skip only the first line (status line)
        start_line = 1
        
        for ln in lines[start_line:]:
            # NEW: Check for tag format first (Type 1 Boolean checkers)
            info_tag_match = info_tag_re.match(ln)
            if info_tag_match:
                message = info_tag_match.group(1).strip()
                infos.append({
                    "index": len(infos) + 1,
                    "detail": message,
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": "N/A"
                })
                continue
            
            waive_tag_match = waive_tag_re.match(ln)
            if waive_tag_match:
                message = waive_tag_match.group(1).strip()
                infos.append({
                    "index": len(infos) + 1,
                    "detail": message,  # Don't add "Waived: " prefix to avoid quotes
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": "Waiver Information[WAIVED]"
                })
                continue
            
            # If we saw "Pass Occurrence:" earlier and now see list items, parse them as infos
            if in_pass_list:
                list_match = pass_list_re.match(ln)
                if list_match:
                    item_text = list_match.group(1).strip()
                    # Create info entry for each list item
                    infos.append({
                        "index": len(infos) + 1,
                        "detail": item_text,
                        "source_line": "N/A",
                        "source_file": "N/A",
                        "reason": "N/A"
                    })
                    continue
                elif ln.strip() == "" or ln.strip().endswith(':'):
                    # Empty line or header line (e.g., "Library Used:"), continue
                    continue
                else:
                    # Non-matching line ends the pass list section
                    in_pass_list = False
            
            # Check if we just passed "Pass Occurrence:" line - start looking for list items
            if "info_occurrence" in data and not in_pass_list and not infos:
                # We have Pass Occurrence but haven't started collecting infos yet
                # Check if current line starts a list
                if pass_list_re.match(ln):
                    in_pass_list = True
                    list_match = pass_list_re.match(ln)
                    if list_match:
                        item_text = list_match.group(1).strip()
                        infos.append({
                            "index": len(infos) + 1,
                            "detail": item_text,
                            "source_line": "N/A",
                            "source_file": "N/A",
                            "reason": "N/A"
                        })
                    continue
                elif ln.strip() and not ln.strip().endswith(':'):
                    # Non-list content, disable pass list mode
                    in_pass_list = False
            
            fm = failure_re.match(ln)
            if fm:
                raw_fail = fm.group(3).strip()
                if raw_fail.endswith('.'):
                    raw_fail = raw_fail[:-1]
                # Handle source_line which can be a number or "Unknown"
                source_line_str = fm.group(4)
                if source_line_str.isdigit():
                    source_line_val: Any = int(source_line_str)
                else:
                    source_line_val = source_line_str
                # Clean reason: remove trailing period
                reason_text = fm.group(6).strip()
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                failures.append({
                    "index": int(fm.group(1)),
                    "fail_status": fm.group(2),
                    "detail": raw_fail,
                    "source_line": source_line_val,
                    "source_file": fm.group(5),
                    "reason": reason_text
                })
                continue
            # Try ultra simplified fail pattern (just "N: Fail: text")
            fm_ultra = fail_ultra_simple_re.match(ln)
            if fm_ultra:
                reason_text = fm_ultra.group(2).strip()
                # Remove trailing period
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                failures.append({
                    "index": int(fm_ultra.group(1)),
                    "fail_status": "Fail",
                    "detail": "N/A",
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": reason_text
                })
                continue
            im_occ = info_occ_re.match(ln)
            if im_occ:
                info_occurrence = int(im_occ.group(1))
                continue
            im = info_re.match(ln)
            if im:
                raw_detail = im.group(2).strip()
                # Remove surrounding quotes and trailing period
                if (raw_detail.startswith('"') and raw_detail.endswith('"')) or (raw_detail.startswith("'") and raw_detail.endswith("'")):
                    raw_detail = raw_detail[1:-1]
                if raw_detail.endswith('.'):
                    raw_detail = raw_detail[:-1]
                # Don't convert to int - keep as string to preserve format
                raw_detail_value = raw_detail
                # Handle source_line for infos
                info_line_str = im.group(3)
                if info_line_str.isdigit():
                    info_line_val: Any = int(info_line_str)
                else:
                    info_line_val = info_line_str
                # Clean reason: remove trailing period
                reason_text = im.group(5).strip()
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                infos.append({
                    "index": int(im.group(1)),
                    "detail": raw_detail_value,
                    "source_line": info_line_val,
                    "source_file": im.group(4),
                    "reason": reason_text
                })
                continue
            # Try simplified info pattern (no "In line" clause)
            im_simple = info_simple_re.match(ln)
            if im_simple:
                raw_detail = im_simple.group(2).strip()
                # Remove surrounding quotes and trailing period
                if (raw_detail.startswith('"') and raw_detail.endswith('"')) or (raw_detail.startswith("'") and raw_detail.endswith("'")):
                    raw_detail = raw_detail[1:-1]
                if raw_detail.endswith('.'):
                    raw_detail = raw_detail[:-1]
                raw_detail_value = raw_detail
                # Clean reason: remove trailing period
                reason_text = im_simple.group(3).strip()
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                infos.append({
                    "index": int(im_simple.group(1)),
                    "detail": raw_detail_value,
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": reason_text
                })
                continue
            # Try ultra simplified info pattern (just "N: Info: text")
            im_ultra = info_ultra_simple_re.match(ln)
            if im_ultra:
                reason_text = im_ultra.group(2).strip()
                # Remove trailing period
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                infos.append({
                    "index": int(im_ultra.group(1)),
                    "detail": "N/A",
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": reason_text
                })
                continue
            wm_occ = warn_occ_re.match(ln)
            if wm_occ:
                warn_occurrence = int(wm_occ.group(1))
                continue
            wm = warn_re.match(ln)
            if wm:
                raw_detail = wm.group(2).strip()
                if (raw_detail.startswith('"') and raw_detail.endswith('"')) or (raw_detail.startswith("'") and raw_detail.endswith("'")):
                    raw_detail = raw_detail[1:-1]
                if raw_detail.endswith('.'):
                    raw_detail = raw_detail[:-1]
                # Don't convert to int - keep as string
                raw_detail_value = raw_detail
                warn_line_str = wm.group(3)
                if warn_line_str.isdigit():
                    warn_line_val: Any = int(warn_line_str)
                else:
                    warn_line_val = warn_line_str
                # Clean reason: remove trailing period
                reason_text = wm.group(5).strip()
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                warnings.append({
                    "index": int(wm.group(1)),
                    "detail": raw_detail_value,
                    "source_line": warn_line_val,
                    "source_file": wm.group(4),
                    "reason": reason_text
                })
                continue
            wm_file = warn_file_re.match(ln)
            if wm_file:
                raw_detail = wm_file.group(2).strip()
                if (raw_detail.startswith('"') and raw_detail.endswith('"')) or (raw_detail.startswith("'") and raw_detail.endswith("'")):
                    raw_detail = raw_detail[1:-1]
                if raw_detail.endswith('.'):
                    raw_detail = raw_detail[:-1]
                # Don't convert to int - keep as string
                raw_detail_value = raw_detail
                # Clean reason: remove trailing period
                reason_text = wm_file.group(4).strip()
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                warnings.append({
                    "index": int(wm_file.group(1)),
                    "detail": raw_detail_value,
                    "source_line": 'N/A',
                    "source_file": wm_file.group(3),
                    "reason": reason_text
                })
                continue
            # Try Type 3 name:reason pattern (e.g., "1: Warn: CELL_NAME : reason text")
            wm_name_reason = warn_name_reason_re.match(ln)
            if wm_name_reason:
                detail_name = wm_name_reason.group(2).strip()
                reason_text = wm_name_reason.group(3).strip()
                # Remove trailing period from reason
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                warnings.append({
                    "index": int(wm_name_reason.group(1)),
                    "detail": detail_name,
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": reason_text
                })
                continue
            # Try ultra simplified warn pattern (just "N: Warn: text")
            wm_ultra = warn_ultra_simple_re.match(ln)
            if wm_ultra:
                reason_text = wm_ultra.group(2).strip()
                # Remove trailing period
                if reason_text.endswith('.'):
                    reason_text = reason_text[:-1]
                warnings.append({
                    "index": int(wm_ultra.group(1)),
                    "detail": "N/A",
                    "source_line": "N/A",
                    "source_file": "N/A",
                    "reason": reason_text
                })
                continue
        if failures:
            data["failures"] = failures
        if info_occurrence is not None:
            data["info_occurrence"] = info_occurrence
        if infos:
            data["infos"] = infos
        if warn_occurrence is not None and "warning_occurrence" not in data:
            data["warning_occurrence"] = warn_occurrence
        if warnings:
            data["warnings"] = warnings
    except Exception:
        pass
    return data

def build_item_entry(item: str,
                     executed: bool,
                     passed: bool,
                     report_info: Dict[str, Any]) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "executed": executed,
        "status": "pass" if passed else "fail"
    }
    if report_info:
        if "description" in report_info:
            entry["description"] = report_info["description"]
        # Failures restructuring
        if "failures" in report_info:
            failures_raw = report_info["failures"]
            if failures_raw:  # Only add failures if there are actual failure items
                failures_list: List[Dict[str, Any]] = []
                for f in failures_raw:
                    # remove fail_status per desired format
                    f2 = {k: v for k, v in f.items() if k != "fail_status"}
                    failures_list.append(f2)
                entry["failures"] = failures_list
        # Infos restructuring
        if "infos" in report_info:
            infos_raw = report_info["infos"]
            if infos_raw:  # Only add infos if there are actual info items
                infos_list: List[Dict[str, Any]] = []
                for inf in infos_raw:
                    infos_list.append(inf)
                entry["infos"] = infos_list
        # Warnings restructuring
        if "warnings" in report_info:
            warnings_raw = report_info["warnings"]
            if warnings_raw:  # Only add warnings if there are actual warning items
                warnings_list: List[Dict[str, Any]] = []
                for w in warnings_raw:
                    warnings_list.append(w)
                entry["warnings"] = warnings_list
    return entry

def write_yaml(struct: Dict[str, Any], yaml_path: Path):
    """
    Write YAML without quotes on detail and reason fields.
    Uses custom writer to avoid PyYAML's automatic quoting.
    """
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    
    def write_value(f, value, indent=0):
        """Write a YAML value with proper indentation."""
        indent_str = '  ' * indent
        
        if value is None or value == 'N/A' or value == '':
            f.write('N/A')
        elif isinstance(value, bool):
            f.write('true' if value else 'false')
        elif isinstance(value, (int, float)):
            f.write(str(value))
        elif isinstance(value, str):
            # Check if string needs quoting:
            # - Contains : followed by space or at end (YAML mapping syntax)
            # - Starts with * (YAML alias/anchor syntax)
            # - Contains double quotes (needs escaping)
            # - Contains backslashes (Windows paths need escaping)
            # - Contains other YAML special characters
            needs_quotes = (': ' in value or 
                          value.endswith(':') or 
                          value.startswith('*') or
                          value.startswith('&') or
                          value.startswith('!') or
                          '"' in value or
                          '\\' in value or
                          "'" in value)
            if needs_quotes:
                # Smart quote selection based on content
                # Priority: single quotes for Windows paths (cleaner, no escaping needed)
                if "'" in value:
                    # Contains single quote - must use double quotes with escaping
                    escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
                    f.write(f'"{escaped_value}"')
                else:
                    # No single quotes - use single quotes (best for Windows paths)
                    # Single quotes in YAML preserve backslashes literally
                    f.write(f"'{value}'")
            else:
                # Write strings without quotes
                f.write(value)
        elif isinstance(value, list):
            if not value:
                f.write('[]\n')
                return
            f.write('\n')
            for item in value:
                if isinstance(item, dict):
                    # For dict items, write first key-value on same line as '-'
                    first_key = True
                    for key, val in item.items():
                        if first_key:
                            f.write(f'{indent_str}- {key}: ')
                            first_key = False
                        else:
                            f.write(f'{indent_str}  {key}: ')
                        
                        # Write the value inline or on next line
                        if isinstance(val, (dict, list)):
                            write_value(f, val, indent + 1)
                        else:
                            write_value(f, val, indent + 1)
                            f.write('\n')
                else:
                    f.write(f'{indent_str}- ')
                    write_value(f, item, indent + 1)
                    f.write('\n')
        elif isinstance(value, dict):
            if not value:
                f.write('{}\n')
                return
            f.write('\n')
            write_dict(f, value, indent)
    
    def write_dict(f, d, indent=0):
        """Write a dictionary as YAML."""
        indent_str = '  ' * indent
        for key, value in d.items():
            f.write(f'{indent_str}{key}: ')
            write_value(f, value, indent + 1)
            # Add newline for simple values and empty collections
            # (dict/list write_value already adds newline at the end)
            if not isinstance(value, (list, dict)) or not value:
                f.write('\n')
    
    with yaml_path.open("w", encoding='utf-8') as f:
        write_dict(f, struct, 0)

def write_summary_yaml(root: Path,
                       stage: str,
                       module: str,
                       items: List[str]) -> Tuple[Path, bool]:
    """
    Build a structured summary YAML for the given module/items.
    
    Returns:
        Tuple of (yaml_path, has_failures) where has_failures is True if any item failed
    """
    base_dir = root / "Check_modules" / module
    summary_dir = base_dir / "outputs"
    if not summary_dir.is_dir():
        raise FileNotFoundError(f"Summary directory not found: {summary_dir}")

    check_items_struct: Dict[str, Any] = {}
    has_failures = False
    
    for item in items:
        log_path = base_dir / "logs" / f"{item}.log"
        report_path = base_dir / "reports" / f"{item}.rpt"   # use .rpt
        executed = log_path.is_file()
        passed = False
        if executed:
            try:
                with log_path.open("r", errors="ignore") as f:
                    content = f.read()
                # Check for FAIL: or [ERROR]: in log
                passed = "FAIL:" not in content and "[ERROR]:" not in content
            except Exception:
                passed = False
        
        # Pass item_id to enable memory cache lookup
        report_info = parse_report(report_path, item_id=item)
        
        # Also check if report has failures - if yes, should be fail
        if report_info and "failures" in report_info and report_info["failures"]:
            passed = False
        
        # Track if any item failed
        if not passed:
            has_failures = True
        
        check_items_struct[item] = build_item_entry(item, executed, passed, report_info)

    struct = {
        "module": module,
        "stage": stage,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "check_items": check_items_struct
    }
    yaml_path = summary_dir / f"{module}.yaml"
    write_yaml(struct, yaml_path)
    print(f"[INFO] Summary written to {yaml_path}")
    return yaml_path, has_failures


if __name__ == '__main__':
    """Command-line interface for generating summary YAML."""
    parser = argparse.ArgumentParser(description='Generate summary YAML from checker reports')
    parser.add_argument('-root', type=str, required=True, help='Project root directory')
    parser.add_argument('-stage', type=str, required=True, help='Stage name (e.g., Initial)')
    parser.add_argument('-module', type=str, required=True, help='Module name (e.g., 1.0_LIBRARY_CHECK)')
    parser.add_argument('-items', type=str, nargs='*', help='Specific items to include (optional)')
    
    args = parser.parse_args()
    root = Path(args.root).resolve()
    
    # Get items list
    if args.items:
        items = args.items
    else:
        # Auto-detect items from logs directory
        module_dir = root / "Check_modules" / args.module / "logs"
        if module_dir.exists():
            items = sorted([f.stem for f in module_dir.glob("IMP-*.log")])
        else:
            print(f"[ERROR] Module directory not found: {module_dir}")
            sys.exit(1)
    
    if not items:
        print(f"[WARN] No items found for module {args.module}")
        sys.exit(0)
    
    print(f"[INFO] Generating summary for {args.module} with {len(items)} items...")
    try:
        yaml_path = write_summary_yaml(root, args.stage, args.module, items)
        print(f"[SUCCESS] Summary YAML generated: {yaml_path}")
    except Exception as e:
        print(f"[ERROR] Failed to generate summary: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
