# IMP-2-0-0-15: List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a

## Overview

**Check ID:** IMP-2-0-0-15**Description:** List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a**Category:** TECHFILE_AND_RULE_DECK_CHECK**Input Files:**

- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\do_qrcrcbest_CCbest_125c.log`

This checker extracts and validates the QRC (Quantus parasitic extraction) technology file reference used in the extraction run. The QRC techfile defines the metal stack configuration and process corner variant (e.g., `16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a`). The checker parses the Quantus QRC log file to locate the technology file path specified in the `process_technology -technology_name` option and extracts the techfile version identifier in the format `<metal_stack>/<corner_variant>`.

---

## Check Logic

### Input Parsing

The checker parses the Cadence Quantus QRC extraction log file to extract the QRC technology file reference.

**Step 1: Locate Technology File Option**
Search for the line matching the pattern `.*Option process_technology -technology_name =`

**Step 2: Extract QRC Path**

- If the value after `=` is empty, extract the qrc tech path in quotes `""` from the next line
- If the value after `=` is not empty, extract the qrc tech path in quotes `""` from the same line
- Store the full path into `qrc_path`

**Step 3: Extract QRC Tech Version**
From the `qrc_path`, extract the QRC version identifier in format `<metal_stack>/<corner_variant>`:

- Example input: `/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcbest/Tech/rcbest_CCbest/qrcTechFile`
- Extracted version: `16M1X1Xb1Xe1Ya1Yb6Y2Yy2Yx2R_SHDMIM_UT/fs_v1d2p4a`
- Store into `qrc_tech`

**Key Patterns:**

```python
# Pattern 1: Locate process_technology option line
pattern1 = r'.*Option\s+process_technology\s+-technology_name\s*='
# Example: "INFO: Option process_technology -technology_name ="

# Pattern 2: Extract metal_stack/corner_variant from full path
pattern3 = r'/QRC/([^/]+/[^/]+)/'
# Example: Extracts "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a" from full path
```

### Detection Logic

**Type 1/4 (No pattern_items):**

- If `qrc_path` can be normally extracted and value exists → **PASS**
- If `qrc_path` cannot be extracted or is empty → **FAIL**
- Output: Display `qrc_tech` value

**Type 2/3 (With pattern_items):**

- Store `pattern_items[0]` into `golden_qrc` (expected QRC tech version)
- If `qrc_tech` == `golden_qrc` → **PASS**
- If `qrc_tech` != `golden_qrc` → **FAIL**
- Output: Display `qrc_tech` (Expected: `golden_qrc`)

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

**Rationale:** This checker validates that the extracted QRC techfile version matches the expected golden value specified in pattern_items. It checks the STATUS (correctness) of the techfile configuration rather than just existence. Only the specified pattern_items are validated - if the extracted `qrc_tech` matches the golden value in pattern_items, it passes; otherwise it fails.

---

## Output Descriptions (CRITICAL - Code Generator Uses These!)

This section defines the output strings used by `build_complete_output()` in the checker code.
**Fill in these values based on the check logic above.**

```python
# ⚠️ CRITICAL: Description & Reason parameter usage by Type (API-026)
# Both DESC and REASON constants are split by Type for semantic clarity:
#   Type 1/4 (Boolean): Use DESC_TYPE1_4 & REASON_TYPE1_4 (emphasize "found/not found")
#   Type 2/3 (Pattern): Use DESC_TYPE2_3 & REASON_TYPE2_3 (emphasize "matched/satisfied")

# Item description for this checker
item_desc = "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "QRC techfile reference found in extraction log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "QRC techfile version matched expected configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "QRC technology file path successfully extracted from process_technology option"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "QRC techfile version matched and validated against golden reference"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "QRC techfile reference not found in extraction log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "QRC techfile version mismatch detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "QRC technology file path not found in process_technology option or extraction log"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "QRC techfile version does not match expected golden reference"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "QRC techfile version mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "QRC techfile version mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused QRC techfile waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding techfile mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: <metal_stack>/<corner_variant> (Expected: <golden_qrc>)
  Example: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a (Expected: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a)

ERROR01 (Violation/Fail items):
  Format: Found: <qrc_tech> | Expected: <golden_qrc>
  Example: Found: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a | Expected: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-15:
  description: "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\do_qrcrcbest_CCbest_125c.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean check to verify QRC techfile reference exists in the extraction log.
PASS if `qrc_tech` can be extracted and has a valid value.
FAIL if `qrc_tech` cannot be extracted or is empty.

**Sample Output (PASS):**

```
Status: PASS
Reason: QRC technology file path successfully extracted from process_technology option
INFO01:
  - 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: QRC technology file path not found in process_technology option or extraction log
ERROR01:
  - QRC techfile reference not found in extraction log
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-15:
  description: "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\do_qrcrcbest_CCbest_125c.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - QRC techfile extraction is for reference purposes"
      - "Note: Missing techfile reference is acceptable for preliminary extraction runs"
```

**CRITICAL Behavior (waivers.value=0):**

- NOTE: Type 1 has NO waiver logic. waive=0 is forced PASS mode only
- IMPORTANT: waive_items uses PLAIN STRINGS (NOT name/reason dict like Type 3/4!)
- waive_items serves as COMMENT ONLY (no matching/filtering logic)
- waive_items content printed as INFO with [WAIVED_INFO] tag
- ALL violations force converted: FAIL→PASS, displayed as INFO with [WAIVED_AS_INFO] tag
- Check ALWAYS returns PASS (violations shown as INFO for tracking)
- Used when: Check is informational only, violations expected/acceptable

**Sample Output (PASS with violations):**

```
Status: PASS  # Always PASS when waivers.value=0
Reason: All violations waived as informational
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: This check is informational only - QRC techfile extraction is for reference purposes"
  - "Note: Missing techfile reference is acceptable for preliminary extraction runs"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - QRC techfile reference not found in extraction log [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-15:
  description: "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
  requirements:
    value: 1
    pattern_items:
      - "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a"  # Expected QRC techfile version
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\do_qrcrcbest_CCbest_125c.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- Description says "List QRC techfile name" with example format `<metal_stack>/<corner_variant>`
- Use TECHFILE VERSION IDENTIFIERS in format: `<metal_stack>/<corner_variant>`
- ✅ CORRECT: "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a"
- ❌ WRONG: Full path "/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcbest/Tech/qrcTechFile"
- ❌ WRONG: Filename only "qrcTechFile"

**Check Behavior:**
Type 2 validates the extracted QRC techfile version against the expected golden value in pattern_items.
PASS if `qrc_tech` matches `pattern_items[0]` (golden_qrc).
FAIL if `qrc_tech` does not match the expected value.

**Sample Output (PASS):**

```
Status: PASS
Reason: QRC techfile version matched and validated against golden reference
INFO01:
  - 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a (Expected: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a)
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: QRC techfile version does not match expected golden reference
ERROR01:
  - Found: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a | Expected: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-15:
  description: "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
  requirements:
    value: 1
    pattern_items:
      - "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\do_qrcrcbest_CCbest_125c.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: QRC techfile version check is informational - multiple valid versions exist"
      - "Note: Techfile version mismatch is acceptable for legacy designs using approved older versions"
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
INFO01 ([WAIVED_INFO] - waive_items as comment):
  - "Explanation: QRC techfile version check is informational - multiple valid versions exist"
  - "Note: Techfile version mismatch is acceptable for legacy designs using approved older versions"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Found: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a | Expected: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-15:
  description: "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
  requirements:
    value: 1
    pattern_items:
      - "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a"  # Expected QRC techfile version
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\do_qrcrcbest_CCbest_125c.log"
  waivers:
    value: 2
    waive_items:
      - name: "17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"  # Waived techfile version
        reason: "Waived - legacy QRC techfile version approved for this design per foundry compatibility"
      - name: "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d1p0a"  # Another waived version
        reason: "Waived - intermediate techfile version used for early design exploration"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:

- BOTH must be at SAME semantic level as description!
- Description says "List QRC techfile name" → Use techfile version format `<metal_stack>/<corner_variant>`
- ✅ pattern_items: ["16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a"] (techfile version)
- ✅ waive_items.name: "17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a" (same level as pattern_items)
- ❌ DO NOT mix: pattern_items with full path, waive_items.name with version only

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern validation logic as Type 2, plus waiver classification:

- Match extracted `qrc_tech` against `pattern_items[0]` (golden_qrc)
- If mismatch found, check against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if `qrc_tech` matches golden_qrc OR all mismatches are waived.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Found: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a | Expected: 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a [WAIVER]
WARN01 (Unused Waivers):
  - 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d1p0a: Waiver entry not matched - no corresponding techfile mismatch found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-15:
  description: "List QRC techfile name. eg: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\do_qrcrcbest_CCbest_125c.log"
  waivers:
    value: 2
    waive_items:
      - name: "17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a"  # Waived techfile version
        reason: "Waived - legacy QRC techfile version approved for this design per foundry compatibility"
      - name: "16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d1p0a"  # Another waived version
        reason: "Waived - intermediate techfile version used for early design exploration"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!

- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (no pattern_items), plus waiver classification:

- Check if QRC techfile reference exists in extraction log
- If violations found (e.g., missing or unexpected techfile), match against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
  PASS if no violations OR all violations are waived.

**Sample Output:**

```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - Found: 17M1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_SHDMIM_UT/fs_v1d0p1a [WAIVER]
WARN01 (Unused Waivers):
  - 16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d1p0a: Waiver entry not matched - no corresponding techfile mismatch found
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-15 --force

# Run individual tests
python IMP-2-0-0-15.py
```

---

## Notes

**Parsing Strategy:**

- The checker uses multi-line context awareness to handle cases where the technology file path may span multiple lines
- The `process_technology -technology_name` option may have the value on the same line or the next line
- The extraction logic handles both quoted and unquoted paths

**QRC Techfile Format:**

- The techfile version identifier follows the format: `<metal_stack>/<corner_variant>`
- Metal stack example: `16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT` (describes metal layer configuration)
- Corner variant example: `fs_v1d2p4a` (describes process corner and version)

**Edge Cases:**

- If the `process_technology` option is not found in the log, the checker will fail
- If the path is found but cannot be parsed to extract the version identifier, the checker will fail
- Multiple techfile references in the same log will use the first occurrence

**Limitations:**

- The checker assumes the QRC log follows standard Cadence Quantus format
- Custom or modified log formats may require pattern adjustments
- The extraction relies on the specific path structure containing `/QRC/<metal_stack>/<corner_variant>/`
