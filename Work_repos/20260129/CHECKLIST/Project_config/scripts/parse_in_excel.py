"""Minimal, dependency-free extraction of checklist rows from an XLSX file.

Only requirements: Python stdlib (zipfile + xml.etree). No pandas / openpyxl.

Assumptions about the BE sheet layout:
  - Column E (5th col, 0-based index 4) contains either module headers or item IDs/text.
  - A module header line in column E starts with a number (e.g. '5.0 - SYNTHESIS CHECK').
  - For data rows: Column E has the item, Column F (index 5) has its description/info.
  - We collect rows until next module header.
"""

import sys, os, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import re, csv

MODULE_HEADER_RE = re.compile(r"^\s*\d+\.?\d*\b")


def _norm_sheet_name(name: str) -> str:
    return re.sub(r"[_\s]+", "", name.lower()) if name else ""

def _norm_module_name(name: str) -> str:
    # Remove parentheses and their contents first
    out = re.sub(r"\([^)]*\)", "", name)
    # Replace '-' and '/' and spaces with underscore, collapse multiple underscores, strip edges
    out = re.sub(r"[-/\s]+", "_", out)
    out = re.sub(r"_+", "_", out)
    out = out.strip("_")
    return out

def _choose_sheet(target: str, sheets):
    # 1. exact
    for s in sheets:
        if s == target:
            return s
    # 2. case-insensitive
    for s in sheets:
        if s.lower() == target.lower():
            return s
    # 3. normalized (remove spaces/underscores)
    tn = _norm_sheet_name(target)
    for s in sheets:
        if _norm_sheet_name(s) == tn:
            return s
    # 4. heuristic: contains 'be' and 'check'
    candidates = [s for s in sheets if 'be' in s.lower() and 'check' in s.lower()]
    return candidates[0] if len(candidates) == 1 else None

def _col_to_index(cell_ref: str) -> int:
    letters = ''.join(ch for ch in cell_ref if ch.isalpha())
    if not letters:
        return -1
    acc = 0
    for ch in letters.upper():
        acc = acc * 26 + (ord(ch) - 64)
    return acc - 1

def _read_sheet_rows(xlsx_path: Path, sheet_name: str):
    with zipfile.ZipFile(str(xlsx_path), 'r') as zf:
        wb = ET.fromstring(zf.read('xl/workbook.xml'))
        ns = {'ns': wb.tag.split('}')[0].strip('{')}
        sheet_elems = wb.findall('.//ns:sheet', ns)
        name_to_rid = {}
        for s in sheet_elems:
            nm = s.attrib.get('name')
            rid = s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id') or s.attrib.get('r:id')
            if nm and rid:
                name_to_rid[nm] = rid
        rels_root = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
        rid_to_target = {}
        for rel in rels_root:
            rid = rel.attrib.get('Id') or rel.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}Id')
            tgt = rel.attrib.get('Target')
            if rid and tgt:
                rid_to_target[rid] = tgt
        chosen = _choose_sheet(sheet_name, list(name_to_rid.keys()))
        if not chosen:
            available = ', '.join(name_to_rid.keys()) or 'NONE'
            raise ValueError("Sheet '%s' not found. Available: %s" % (sheet_name, available))
        sheet_rel = rid_to_target.get(name_to_rid[chosen])
        if not sheet_rel:
            raise ValueError("Failed to resolve sheet rel for '%s'" % chosen)
        sheet_path = 'xl/' + sheet_rel
        if sheet_path not in zf.namelist():
            raise ValueError("Sheet path '%s' missing in archive" % sheet_path)
        shared_strings = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            sroot = ET.fromstring(zf.read('xl/sharedStrings.xml'))
            for si in sroot:
                texts = []
                for node in si.iter():
                    if node.tag.endswith('}t') or node.tag=='t':
                        if node.text: texts.append(node.text)
                shared_strings.append(''.join(texts))
        sroot = ET.fromstring(zf.read(sheet_path))
        for row in sroot.iter():
            if not (row.tag.endswith('}row') or row.tag=='row'): continue
            cells = {}
            maxc = -1
            for c in row:
                if not (c.tag.endswith('}c') or c.tag=='c'): continue
                ref = c.attrib.get('r') or ''
                ci = _col_to_index(ref)
                t = c.attrib.get('t')
                val = ''
                v_elem = None
                for ch in c:
                    if ch.tag.endswith('}v') or ch.tag=='v': v_elem = ch; break
                if v_elem is not None and v_elem.text is not None:
                    raw = v_elem.text
                    if t == 's':
                        try:
                            idx = int(raw)
                            val = shared_strings[idx] if 0 <= idx < len(shared_strings) else raw
                        except Exception:
                            val = raw
                    else:
                        val = raw
                cells[ci] = val
                if ci > maxc: maxc = ci
            if cells:
                yield [cells.get(i,'') for i in range(maxc+1)]

def parse_in_excel(stage, excel_file, output_dir=None, sheet_name='BE_check', verbose=False):
    excel_file = Path(excel_file)
    if output_dir is None:
        output_dir = excel_file.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    override = os.environ.get('CHECKLIST_SHEET')
    if override:
        sheet_name = override
        if verbose:
            print("Sheet override via CHECKLIST_SHEET=", sheet_name, file=sys.stderr)
    if not excel_file.exists():
        print("ERROR: Excel file not found:", excel_file, file=sys.stderr)
        return None
    try:
        rows = list(_read_sheet_rows(excel_file, sheet_name))
    except Exception as e:
        print("ERROR: cannot parse sheet:", e, file=sys.stderr)
        return None
    checklist = []
    current_module = None
    
    for r in rows:
        colE = r[4].strip() if len(r) > 4 and isinstance(r[4], str) else (str(r[4]).strip() if len(r) > 4 and r[4] is not None else '')
        # Normalize Info field: replace newline(s) with ' '
        if len(r) > 5 and r[5] is not None:
            colF_raw = str(r[5])
            # Replace any CR/LF sequences with a single space and collapse repeats
            colF = re.sub(r'[\r\n]+', ' ', colF_raw)
            colF = re.sub(r' {2,}', ' ', colF).strip(' ')
        else:
            colF = ''
        if colE and MODULE_HEADER_RE.match(colE):
            current_module = colE.strip()
            current_module = _norm_module_name(current_module)
            continue
        if not current_module:
            continue
        if not colE or not colF:
            continue
        checklist.append({'Check_modules': current_module, 'Item': colE, 'Info': colF})
    
    out_csv = output_dir / 'CheckList.csv'
    try:
        if out_csv.exists():
            try: out_csv.unlink()
            except Exception: pass
        with out_csv.open('w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Check_modules','Item','Info'])
            for row in checklist:
                w.writerow([row['Check_modules'], row['Item'], row['Info']])
        if verbose:
            print(f"Extracted {len(checklist)} checklist rows", file=sys.stderr)
        print(f"Wrote {out_csv} with {len(checklist)} rows")
    except Exception as e:
        print("ERROR: cannot write CSV:", e, file=sys.stderr)
        return None
    return out_csv