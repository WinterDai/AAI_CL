#!/usr/bin/env python3
import sys, csv, re
from pathlib import Path
from collections import OrderedDict

# Header synonyms
SECTION_KEYS = {"checkmodules", "section"}
ID_KEYS = {"id", "checkid", "itemid", "ruleid", "impid"}
DESC_KEYS = {"description", "item", "question", "text", "desc", "content"}
INFO_KEYS = {"info", "info01", "prompt_info", "promptinfo"}
WARN_KEYS = {"warn", "warn01", "warning", "prompt_warn", "promptwarn"}

YAML_FILENAME = "CheckList_Index.yaml"

def norm_header(s):
    if s is None: return ""
    return re.sub(r"[ _\-]+", "", str(s).strip().lower())

def find_header_indices(header_row):
    norm = [norm_header(h) for h in header_row]
    def f(cands):
        for i,n in enumerate(norm):
            if n in cands: return i
        return None
    section = f(SECTION_KEYS)
    cid     = f(ID_KEYS)
    desc    = f(DESC_KEYS)
    info    = f(INFO_KEYS)
    warn    = f(WARN_KEYS)
    if desc is None:
        raise ValueError("No 'Item' (description) column found")
    return {"section":section,"id":cid,"desc":desc,"info":info,"warn":warn}

def load_rows_from_csv(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f):
            rows.append(r)
    header_idx = None
    idxs = None
    for i,r in enumerate(rows):
        if not any(c.strip() for c in map(str,r) if c): continue
        try:
            idxs_try = find_header_indices(r)
            idxs = idxs_try
            header_idx = i
            break
        except ValueError:
            continue
    if idxs is None:
        raise ValueError("Header row not found")
    return idxs, rows[header_idx+1:]

def _norm_section_name(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[-/\s]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_").rstrip(":")

def parse_checklist(csv_path: Path):
    idxs, data = load_rows_from_csv(csv_path)
    sections = OrderedDict()
    current = None
    id_from_item_re = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*[:：]\s*(.+)$")
    for row in data:
        def g(i):
            return row[i] if (i is not None and i < len(row)) else ""
        raw_sec = g(idxs["section"]).strip()
        raw_id  = g(idxs["id"]).strip()
        raw_item= g(idxs["desc"]).strip()
        raw_info= g(idxs["info"]).strip()
        if raw_sec:
            current = _norm_section_name(raw_sec)
        if not current or not raw_item:
            continue
        cid = raw_id
        desc = raw_item
        if not cid:
            m = id_from_item_re.match(raw_item)
            if m:
                cid = m.group(1).strip()
                desc = m.group(2).strip()
        # Fallback: if still no id, use the item text itself as id
        if not cid:
            cid = raw_item
        # If description ended up empty but info column has text, use info
        if (not desc or desc == cid) and raw_info and raw_info != desc:
            desc = raw_info
        if not cid:
            continue
        sec = sections.setdefault(current, OrderedDict())
        sec.setdefault("checklist_item", []).append(OrderedDict([(cid, desc)]))
    return sections

def find_checklist_csv(stage_latest_dir: Path) -> Path:
    p = stage_latest_dir / "CheckList.csv"
    if not p.exists():
        raise FileNotFoundError(p)
    return p

def load_prompt_items_simple(prompt_csv: Path):
    if not prompt_csv.exists():
        return []
    with prompt_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows: return []
    header = rows[0]
    norm = [norm_header(h) for h in header]
    def idx(name_set):
        for i,h in enumerate(norm):
            if h in name_set: return i
        return -1
    idx_mod = idx({"checkmodules","section"})
    idx_item= idx({"item","itemname"})
    idx_info= idx({"info"})
    if idx_item < 0 or idx_info < 0 or idx_mod < 0:
        return []
    out=[]
    for r in rows[1:]:
        if len(r)<=max(idx_mod,idx_item,idx_info): continue
        mod = _norm_section_name(r[idx_mod].strip()) if r[idx_mod].strip() else ""
        it  = r[idx_item].strip()
        inf = r[idx_info].strip()
        if mod and it and inf:
            out.append((mod,it,inf))
    return out

def write_yaml(out_path: Path, sections: OrderedDict):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for sec, body in sections.items():
            f.write(f"{sec}:\n")
            # checklist items
            f.write("  checklist_item:\n")
            for item in body.get("checklist_item", []):
                for k,v in item.items():
                    f.write(f"    - {k}: #{v}\n")
            # prompt items
            f.write("  prompt_item:\n")
            for p in body.get("prompt_item", []):
                for k,v in p.items():
                    f.write(f"    - {k}: #{v}\n")

def main():
    if len(sys.argv) < 3:
        print("Usage: get_checklist.py <Stage> <ChecklistExcelFile>")
        return 2
    stage = sys.argv[1]
    excel_name = sys.argv[2]

    script_dir = Path(__file__).resolve().parent
    proj_cfg = script_dir.parents[0]
    
    coll_latest = proj_cfg / "collaterals" / stage / "latest"
    prep_latest = proj_cfg / "prep_config" / stage / "latest"
    excel_path = coll_latest / excel_name
    if not excel_path.exists():
        print(f"ERROR: Excel file missing: {excel_path}")
        return 2

    # Expect existing CheckList.csv already produced by parse_in_excel
    try:
        checklist_csv = find_checklist_csv(coll_latest)
    except Exception as e:
        print(f"ERROR: {e}")
        return 3

    sections = parse_checklist(checklist_csv)

    # Load prompt items PER module
    prompt_csv = coll_latest / "promp_item.csv"
    prompts = load_prompt_items_simple(prompt_csv)
    # Build map: module -> list of OrderedDict
    mod_map = {}
    for mod, item, info in prompts:
        mod_map.setdefault(mod, []).append(OrderedDict([(item, info)]))

    # Attach ONLY its own prompt items
    for sec in sections.keys():
        sections[sec]["prompt_item"] = mod_map.get(sec, [])

    out_yaml = prep_latest / YAML_FILENAME
    write_yaml(out_yaml, sections)
    print(f"Generated {out_yaml}")
    return 0

if __name__ == "__main__":
    sys.exit(main())