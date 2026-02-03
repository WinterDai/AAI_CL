# IMP-11-0-0-07: Confirm all the PGV views are present in the EMIR scripts.

## Overview

**Check ID:** IMP-11-0-0-07  
**Description:** Confirm all the PGV views are present in the EMIR scripts.  
**Category:** Power Analysis Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out`

This checker validates that all required PGV (Power Grid View) views are present in the EMIR (ElectroMigration and IR-drop) analysis scripts by examining the missing PGV report. It identifies cells without PGV views and determines if they can be waived based on cell type patterns (*DTCD*, *_BEOL, *_FEOL). The check passes when no missing PGV views exist or all missing views are covered by approved waivers.

---

## Check Logic

### Input Parsing
The input file `missingLibModelCell.out` contains the total count of missing PGV views and lists the cell names that lack PGV views. The file format includes a summary line with the total count and individual cell entries.

**Key Patterns (shared across all types):**
```python
# Pattern 1: Extract total missing PGV count
pattern_total = r'Total\s+missing\s+PGV\s+views?\s*:\s*(\d+)'
# Example: "Total missing PGV views: 5"

# Pattern 2: Extract missing PGV cell names
pattern_cell = r'^\s*([A-Za-z0-9_]+)\s*$'
# Example: "CORE65GPSVT_DTCD_cell1"

# Pattern 3: General waiver patterns for cell types
pattern_dtcd = r'.*DTCD.*'
pattern_beol = r'.*_BEOL$'
pattern_feol = r'.*_FEOL$'
# Examples: "LIB_DTCD_CELL", "CELL_BEOL", "CELL_FEOL"
```

### Detection Logic
1. Read input file `missingLibModelCell.out`
2. Parse total missing PGV count from summary line
3. Extract all missing PGV cell names from the report
4. Print all missing PGV cells as INFO for tracking
5. Check if missing cells match general waiver patterns (*DTCD*, *_BEOL, *_FEOL)
6. Match remaining cells against user-provided waive_items
7. Determine PASS/FAIL:
   - PASS: Total missing PGV = 0, OR all missing cells are waived (general patterns + explicit waivers)
   - FAIL: Missing PGV cells exist that are not covered by waivers

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - 存在性检查
**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["item_A", "item_B", "item_C"]
Input file contains: item_A, item_B

Result:
  found_items:   item_A, item_B    ← Pattern found in file
  missing_items: item_C            ← Pattern NOT found in file

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

### Mode 2: `status_check` - 状态检查  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["port_A", "port_B"]
Input file contains: port_A(fixed), port_B(unfixed), port_C(unfixed)

Result:
  found_items:   port_A            ← Pattern matched AND status correct
  missing_items: port_B            ← Pattern matched BUT status wrong
  (port_C not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker examines the status of PGV views (present vs. missing). The input file reports cells with missing PGV views, and we validate whether these missing views are acceptable (waivable) or not. We only care about cells that appear in the missing PGV report, not all possible cells in the design.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Confirm all the PGV views are present in the EMIR scripts."

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "All PGV views are present in EMIR scripts"
found_desc_type2_3 = "All missing PGV views are covered by waivers"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "No missing PGV views found in missingLibModelCell.out report"
found_reason_type2_3 = "All missing PGV cells are waived (general patterns or explicit waivers)"

# FAIL case descriptions
missing_desc_type1_4 = "Missing PGV views detected in EMIR scripts"
missing_desc_type2_3 = "Unwaived missing PGV views found"

# FAIL reasons
missing_reason_type1_4 = "Missing PGV views found in missingLibModelCell.out report"
missing_reason_type2_3 = "Missing PGV cells not covered by waiver list"

# WAIVED case descriptions
waived_desc = "Missing PGV view waived"
waived_base_reason = "Missing PGV view waived - No PGV view is required for this type of cell"

# UNUSED waivers
unused_desc = "Unused PGV waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding missing PGV cell found in report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[cell_name]"
  Example: "CORE65GPSVT_DTCD_CELL1"

ERROR01 (Violation/Fail items):
  Format: "[cell_name]"
  Example: "CUSTOM_CELL_NO_PGV"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-07:
  description: "Confirm all the PGV views are present in the EMIR scripts."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean checks (file exists? config valid?).
PASS/FAIL based on checker's own validation logic.

**Sample Output (PASS):**
```
Status: PASS
Reason: No missing PGV views found in missingLibModelCell.out report

Log format (item_id.log):
INFO01:
  - Total missing PGV views: 0

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: Total missing PGV views: 0. In line 1, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: No missing PGV views found in missingLibModelCell.out report
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Missing PGV views found in missingLibModelCell.out report

Log format (item_id.log):
ERROR01:
  - CORE65GPSVT_CUSTOM_CELL1
  - CORE65GPSVT_CUSTOM_CELL2

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: CORE65GPSVT_CUSTOM_CELL1. In line 3, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV views found in missingLibModelCell.out report
2: Fail: CORE65GPSVT_CUSTOM_CELL2. In line 4, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV views found in missingLibModelCell.out report
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-07:
  description: "Confirm all the PGV views are present in the EMIR scripts."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: PGV view check is informational only for this design phase"
      - "Note: Missing PGV views will be addressed in final EMIR analysis"
```

**Sample Output (PASS with violations):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: PGV view check is informational only for this design phase"
  - "Note: Missing PGV views will be addressed in final EMIR analysis"
INFO02:
  - CORE65GPSVT_CUSTOM_CELL1
  - CORE65GPSVT_CUSTOM_CELL2

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: PGV view check is informational only for this design phase. [WAIVED_INFO]
2: Info: Note: Missing PGV views will be addressed in final EMIR analysis. [WAIVED_INFO]
3: Info: CORE65GPSVT_CUSTOM_CELL1. In line 3, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV views found in missingLibModelCell.out report [WAIVED_AS_INFO]
4: Info: CORE65GPSVT_CUSTOM_CELL2. In line 4, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV views found in missingLibModelCell.out report [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-07:
  description: "Confirm all the PGV views are present in the EMIR scripts."
  requirements:
    value: 0
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: All missing PGV cells are waived (general patterns or explicit waivers)

Log format (item_id.log):
INFO01:
  - Total missing PGV views: 0

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: Total missing PGV views: 0. In line 1, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: All missing PGV cells are waived (general patterns or explicit waivers)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-11-0-0-07:
  description: "Confirm all the PGV views are present in the EMIR scripts."
  requirements:
    value: 0
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: PGV view validation is informational during early design stages"
      - "Note: All missing PGV views are acceptable for preliminary EMIR analysis"
```

**CRITICAL Behavior (waivers.value=0):**
- NOTE: Type 2 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL errors/mismatches force converted: ERROR→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (errors shown as INFO for tracking)
- Used when: Pattern check is informational, mismatches expected

**Sample Output (PASS with mismatches):**
```
Status: PASS  # Always PASS when waivers.value=0
Reason: All mismatches waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: PGV view validation is informational during early design stages"
  - "Note: All missing PGV views are acceptable for preliminary EMIR analysis"
INFO02:
  - CORE65GPSVT_CUSTOM_CELL1
  - CORE65GPSVT_CUSTOM_CELL2

Report format (item_id.rpt):
Info Occurrence: 4
1: Info: Explanation: PGV view validation is informational during early design stages. [WAIVED_INFO]
2: Info: Note: All missing PGV views are acceptable for preliminary EMIR analysis. [WAIVED_INFO]
3: Info: CORE65GPSVT_CUSTOM_CELL1. In line 3, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV cells not covered by waiver list [WAIVED_AS_INFO]
4: Info: CORE65GPSVT_CUSTOM_CELL2. In line 4, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV cells not covered by waiver list [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-07:
  description: "Confirm all the PGV views are present in the EMIR scripts."
  requirements:
    value: 0
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out"
  waivers:
    value: 2
    waive_items:
      - name: "CORE65GPSVT_CUSTOM_CELL1"  # Object NAME to exempt, NOT pattern value
        reason: "Waived - Custom cell without PGV requirement per design team"
      - name: "CORE65GPSVT_CUSTOM_CELL2"
        reason: "Waived - Legacy cell excluded from EMIR analysis"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- pattern_items = VALUES to match (versions, status, conditions)
- waive_items.name = OBJECT NAMES to exempt (libraries, modules, views, files)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Match found_items against waive_items
- Unwaived items → ERROR (need fix)
- Waived items → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all found_items (violations) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (item_id.log):
INFO01:
  - CORE65GPSVT_CUSTOM_CELL1
  - CORE65GPSVT_DTCD_CELL1
WARN01:
  - CORE65GPSVT_CUSTOM_CELL2

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: CORE65GPSVT_CUSTOM_CELL1. In line 3, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV view waived - No PGV view is required for this type of cell: Waived - Custom cell without PGV requirement per design team [WAIVER]
2: Info: CORE65GPSVT_DTCD_CELL1. In line 4, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV view waived - No PGV view is required for this type of cell: General waiver pattern *DTCD* matched [WAIVER]
Warn Occurrence: 1
1: Warn: CORE65GPSVT_CUSTOM_CELL2. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Waiver not matched - no corresponding missing PGV cell found in report: Waived - Legacy cell excluded from EMIR analysis [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-11-0-0-07:
  description: "Confirm all the PGV views are present in the EMIR scripts."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out"
  waivers:
    value: 2
    waive_items:
      - name: "CORE65GPSVT_CUSTOM_CELL1"  # ⚠️ MUST match Type 3 waive_items
        reason: "Waived - Custom cell without PGV requirement per design team"
      - name: "CORE65GPSVT_CUSTOM_CELL2"
        reason: "Waived - Legacy cell excluded from EMIR analysis"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (item_id.log):
INFO01:
  - CORE65GPSVT_CUSTOM_CELL1
  - CORE65GPSVT_DTCD_CELL1
WARN01:
  - CORE65GPSVT_CUSTOM_CELL2

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: CORE65GPSVT_CUSTOM_CELL1. In line 3, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV view waived - No PGV view is required for this type of cell: Waived - Custom cell without PGV requirement per design team [WAIVER]
2: Info: CORE65GPSVT_DTCD_CELL1. In line 4, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Missing PGV view waived - No PGV view is required for this type of cell: General waiver pattern *DTCD* matched [WAIVER]
Warn Occurrence: 1
1: Warn: CORE65GPSVT_CUSTOM_CELL2. In line 0, ${CHECKLIST_ROOT}/IP_project_folder/reports/11.0/missingLibModelCell.out: Waiver not matched - no corresponding missing PGV cell found in report: Waived - Legacy cell excluded from EMIR analysis [WAIVER]
```