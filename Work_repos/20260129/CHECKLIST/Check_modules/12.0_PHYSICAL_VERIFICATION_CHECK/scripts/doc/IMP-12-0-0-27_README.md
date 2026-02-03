# IMP-12-0-0-27: Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?

## Overview

**Check ID:** IMP-12-0-0-27
**Description:** Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?
**Category:** Physical Verification
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv`

This checker validates that bump locations extracted from GDS/OAS layout match the package requirements. It parses bump coordinates from a CSV file (containing fields like Bump_ID, Name, Center_X, Center_Y, Width, Height, Area, Text_Distance), extracts the relevant location data (Name, Center_X, Center_Y), and compares unique bump positions against design requirements to ensure package-to-chip alignment is correct.

---

## Check Logic

### Input Parsing

Parse the CSV file containing bump location data extracted from GDS/OAS layout. The first line is a header indicating field names, and subsequent lines contain bump data.

**Key Patterns (shared across all types):**

```python
# Pattern 1: CSV header line to identify field positions
header_pattern = r'^Bump_ID,Name,Center_X,Center_Y,Width,Height,Area,Text_Distance'
# Example: "Bump_ID,Name,Center_X,Center_Y,Width,Height,Area,Text_Distance"

# Pattern 2: CSV data line with bump information
data_pattern = r'^[^,]+,([^,]+),([0-9.]+),([0-9.]+),'
# Example: "1,VSS,1234.5678,2345.6789,80.0,80.0,6400.0,5.2"
# Captures: Name (field 2), Center_X (field 3), Center_Y (field 4)

# Pattern 3: Formatted bump location
location_format = r'^\w+:\s*\d+\.\d+\s+\d+\.\d+$'
# Example: "VSS: 1234.5678 2345.6789"
```

### Detection Logic

1. Read the CSV input file line by line
2. Parse the header line to confirm field structure (Bump_ID, Name, Center_X, Center_Y, etc.)
3. For each data line, extract fields 2, 3, 4 (Name, Center_X, Center_Y using 1-based indexing)
4. Store each bump as a dictionary in a list: `[{"VSS": "1234.5678 2345.6789"}, {"PAD_0": "5678.1234 6789.2345"}, ...]`
5. Remove duplicate entries from the list (unique bump locations only)
6. Compare the unique bump location list against requirements
7. PASS if all required bump locations are found with correct coordinates; FAIL if any mismatches or missing bumps detected

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

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

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates that all required bump locations from package specifications exist in the extracted GDS/OAS bump data. The pattern_items represent expected bump locations (name and coordinates) that must be present in the CSV file for package-to-chip alignment verification.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.

```python
# Item description for this checker
item_desc = "Bump location comparison between package requirements and GDS/OAS extraction"

# PASS case descriptions - Split by Type semantics (API-026)
found_desc_type1_4 = "All bump locations validated successfully in GDS extraction report"
found_desc_type2_3 = "Required bump locations matched in GDS extraction (all bumps verified)"

# PASS reasons - Split by Type semantics
found_reason_type1_4 = "Bump location data extracted from GDS/OAS matches package requirements"
found_reason_type2_3 = "All required bump locations found and validated in GDS extraction report"

# FAIL case descriptions
missing_desc_type1_4 = "Bump location validation failed - mismatches detected in GDS extraction"
missing_desc_type2_3 = "Required bump locations not satisfied - missing or mismatched bumps detected"

# FAIL reasons
missing_reason_type1_4 = "Bump location mismatches found between package requirements and GDS extraction"
missing_reason_type2_3 = "Required bump locations missing or coordinates mismatched in GDS extraction report"

# WAIVED case descriptions
waived_desc = "Bump location mismatch waived"
waived_base_reason = "Bump location verification waived per package design team approval"

# UNUSED waivers
unused_desc = "Unused bump location waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding bump location mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "{bump_name}: {x_coord} {y_coord}"
  Example: "VSS: 1234.5678 2345.6789"
  Example: "PAD_0: 5678.1234 6789.2345"

ERROR01 (Violation/Fail items):
  Format: "{bump_name}: {x_coord} {y_coord} (expected: {expected_x} {expected_y})"
  Example: "VDD: 1111.2222 3333.4444 (expected: 1111.2223 3333.4445)"
  Example: "PAD_5: missing in GDS extraction"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-27:
  description: "Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv"
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
Reason: Bump location data extracted from GDS/OAS matches package requirements

Log format (item_id.log):
INFO01:
  - VSS: 1234.5678 2345.6789
  - VDD: 2345.6789 3456.7890
  - PAD_0: 5678.1234 6789.2345

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: VSS: 1234.5678 2345.6789. In line 2, tv_chip_gds_bump.csv: Bump location data extracted from GDS/OAS matches package requirements
2: Info: VDD: 2345.6789 3456.7890. In line 3, tv_chip_gds_bump.csv: Bump location data extracted from GDS/OAS matches package requirements
3: Info: PAD_0: 5678.1234 6789.2345. In line 4, tv_chip_gds_bump.csv: Bump location data extracted from GDS/OAS matches package requirements
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Bump location mismatches found between package requirements and GDS extraction

Log format (item_id.log):
ERROR01:
  - VDD: 1111.2222 3333.4444 (expected: 1111.2223 3333.4445)
  - PAD_5: missing in GDS extraction

Report format (item_id.rpt):
Fail Occurrence: 2
1: Fail: VDD: 1111.2222 3333.4444 (expected: 1111.2223 3333.4445). In line 5, tv_chip_gds_bump.csv: Bump location mismatches found between package requirements and GDS extraction
2: Fail: PAD_5: missing in GDS extraction. In line N/A, tv_chip_gds_bump.csv: Bump location mismatches found between package requirements and GDS extraction
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-12-0-0-27:
  description: "Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: Bump location check is informational during early design phase"
      - "Note: Minor coordinate mismatches acceptable for pre-tapeout validation"
```

**Sample Output (PASS with violations):**

```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational

Log format (item_id.log):
INFO01:
  - "Explanation: Bump location check is informational during early design phase"
  - "Note: Minor coordinate mismatches acceptable for pre-tapeout validation"
INFO02:
  - VDD: 1111.2222 3333.4444 (expected: 1111.2223 3333.4445)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Bump location check is informational during early design phase. [WAIVED_INFO]
2: Info: Note: Minor coordinate mismatches acceptable for pre-tapeout validation. [WAIVED_INFO]
3: Info: VDD: 1111.2222 3333.4444 (expected: 1111.2223 3333.4445). In line 5, tv_chip_gds_bump.csv: Bump location mismatches found between package requirements and GDS extraction [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-27:
  description: "Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
  requirements:
    value: 3
    pattern_items:
      - VSS: 1234.5678 2345.6789
      - VDD: 2345.6789 3456.7890
      - PAD_0: 5678.1234 6789.2345
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv"
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
Reason: All required bump locations found and validated in GDS extraction report

Log format (item_id.log):
INFO01:
  - VSS: 1234.5678 2345.6789
  - VDD: 2345.6789 3456.7890
  - PAD_0: 5678.1234 6789.2345

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: VSS: 1234.5678 2345.6789. In line 2, tv_chip_gds_bump.csv: All required bump locations found and validated in GDS extraction report
2: Info: VDD: 2345.6789 3456.7890. In line 3, tv_chip_gds_bump.csv: All required bump locations found and validated in GDS extraction report
3: Info: PAD_0: 5678.1234 6789.2345. In line 4, tv_chip_gds_bump.csv: All required bump locations found and validated in GDS extraction report
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-12-0-0-27:
  description: "Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
  requirements:
    value: 0
    pattern_items:
      - VSS: 1234.5678 2345.6789
      - VDD: 2345.6789 3456.7890
      - PAD_0: 5678.1234 6789.2345
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode
    waive_items:  # IMPORTANT: Use PLAIN STRING format
      - "Explanation: Bump location verification is informational only for this design phase"
      - "Note: Package substrate design not finalized, coordinate mismatches expected"
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
  - "Explanation: Bump location verification is informational only for this design phase"
  - "Note: Package substrate design not finalized, coordinate mismatches expected"
INFO02:
  - PAD_0: 5678.1234 6789.2345 (not found in GDS)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Bump location verification is informational only for this design phase. [WAIVED_INFO]
2: Info: Note: Package substrate design not finalized, coordinate mismatches expected. [WAIVED_INFO]
3: Info: PAD_0: 5678.1234 6789.2345 (not found in GDS). In line N/A, tv_chip_gds_bump.csv: Required bump locations missing or coordinates mismatched in GDS extraction report [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-27:
  description: "Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
  requirements:
    value: 3
    pattern_items:
      - VSS: 1234.5678 2345.6789
      - VDD: 2345.6789 3456.7890
      - PAD_0: 5678.1234 6789.2345
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv"
  waivers:
    value: 2
    waive_items:
      - name: "VDD"
        reason: "Waived - VDD bump location adjusted per package team ECO-2024-001"
      - name: "PAD_0"
        reason: "Waived - PAD_0 coordinates updated for substrate routing optimization"
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
  - VDD
  - PAD_0
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: VDD. In line 3, tv_chip_gds_bump.csv: Bump location verification waived per package design team approval: Waived - VDD bump location adjusted per package team ECO-2024-001 [WAIVER]
2: Info: PAD_0. In line 4, tv_chip_gds_bump.csv: Bump location verification waived per package design team approval: Waived - PAD_0 coordinates updated for substrate routing optimization [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-12-0-0-27:
  description: "Confirm Package to Chip comparison passes (bump excel vs bump location in gds/oas)?"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/tv_chip_gds_bump.csv"
  waivers:
    value: 2
    waive_items:
      - name: "VDD"
        reason: "Waived - VDD bump location adjusted per package team ECO-2024-001"
      - name: "PAD_0"
        reason: "Waived - PAD_0 coordinates updated for substrate routing optimization"
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
  - VDD
  - PAD_0
WARN01:
  - (none - all waivers used)

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: VDD. In line 3, tv_chip_gds_bump.csv: Bump location verification waived per package design team approval: Waived - VDD bump location adjusted per package team ECO-2024-001 [WAIVER]
2: Info: PAD_0. In line 4, tv_chip_gds_bump.csv: Bump location verification waived per package design team approval: Waived - PAD_0 coordinates updated for substrate routing optimization [WAIVER]
Warn Occurrence: 0
```
