# IMP-2-0-0-13: List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs

## Overview

**Check ID:** IMP-2-0-0-13  
**Description:** List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs  
**Category:** TECHFILE_AND_RULE_DECK_CHECK  
**Input Files:** 
- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\command_list.btxt`

This checker validates the SPICE model version used for Power Grid Verification (PGV) generation. It extracts the SPICE model path from the command list file, parses the model version identifier (e.g., `tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs`), and reports the version used. For Type 2/3 configurations, it validates against expected golden model versions.

---

## Check Logic

### Input Parsing

The checker parses the `command_list.btxt` file to extract SPICE model information:

**Key Patterns:**
```python
# Pattern 1: Extract SPICE model path from command_list.btxt
pattern1 = r'spice_models\s+(.+)'
# Example: "spice_models /process/tsmcN5/data/g/PDK/tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"
# Captures: /process/tsmcN5/data/g/PDK/tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs

# Pattern 2: Extract model version from absolute path
# From path like: /process/tsmcN5/data/g/PDK/tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs
# Extract: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs
pattern2 = r'PDK/(.+)$'
# Example extraction: "tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"
```

### Detection Logic

**Step 1: Parse SPICE Model Path**
- Search for lines matching `spice_models *` pattern in `command_list.btxt`
- Extract the absolute model path after "spice_models" keyword
- Store in `spice_path` variable

**Step 2: Extract Model Version**
- From `spice_path`, extract the model version identifier
- Pattern: Extract substring after "PDK/" to get relative model path
- Example: `/process/tsmcN5/data/g/PDK/tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs` → `tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs`
- Store in `spice_model` variable

**Step 3: Validation Logic (Type-Dependent)**

**Type 1/4 (Boolean Check):**
- If `spice_path` can be extracted and has a valid value → **PASS**
- If `spice_path` is empty or not found → **FAIL**
- Output: Report the extracted `spice_model` version

**Type 2/3 (Pattern Check):**
- If `pattern_items` is not empty:
  - Store `pattern_items[0]` into `golden_spice` (expected model version)
  - Compare `spice_model` with `golden_spice`
  - If `spice_model` == `golden_spice` → **PASS**
  - If `spice_model` != `golden_spice` → **FAIL**
- Output format: `spice_model` (Expected: `golden_spice`)

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

**Rationale:** This checker validates the SPICE model version against expected golden values. The `pattern_items` represent expected model version identifiers (e.g., `tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs`). The checker extracts the actual model version from the command list and compares it against the golden value. Only the matched pattern is output with its validation status (match/mismatch), making this a status check rather than an existence check.

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
item_desc = "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "SPICE model version found in command list"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "SPICE model version matched expected golden value"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "SPICE model path successfully extracted from command_list.btxt"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "SPICE model version matched and validated against golden reference"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "SPICE model version not found in command list"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "SPICE model version does not match expected golden value"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "SPICE model path not found in command_list.btxt or spice_models command missing"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "SPICE model version mismatch - actual version does not satisfy expected golden reference"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "SPICE model version mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "SPICE model version mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused SPICE model waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding SPICE model version mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "SPICE Model: [spice_model] (Expected: [golden_spice])" for Type 2/3
          "SPICE Model: [spice_model]" for Type 1/4
  Example: "SPICE Model: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs (Expected: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs)"
           "SPICE Model: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"

ERROR01 (Violation/Fail items):
  Format: "SPICE Model Mismatch: Found=[actual_model], Expected=[golden_spice]" for Type 2/3
          "SPICE Model Not Found: spice_models command missing in command_list.btxt" for Type 1/4
  Example: "SPICE Model Mismatch: Found=tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs, Expected=tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-13:
  description: "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\command_list.btxt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation to check if SPICE model path exists in command_list.btxt.
PASS if `spice_models` command is found and model path can be extracted.
FAIL if `spice_models` command is missing or path extraction fails.

**Sample Output (PASS):**
```
Status: PASS
Reason: SPICE model path successfully extracted from command_list.btxt
INFO01:
  - SPICE Model: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: SPICE model path not found in command_list.btxt or spice_models command missing
ERROR01:
  - SPICE Model Not Found: spice_models command missing in command_list.btxt
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-13:
  description: "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\command_list.btxt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - SPICE model version is reported for reference"
      - "Note: SPICE model path extraction failures are acceptable during early design stages"
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
  - "Explanation: This check is informational only - SPICE model version is reported for reference"
  - "Note: SPICE model path extraction failures are acceptable during early design stages"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - SPICE Model Not Found: spice_models command missing in command_list.btxt [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-13:
  description: "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
  requirements:
    value: 1
    pattern_items:
      - "tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"  # Golden SPICE model version
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\command_list.btxt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "List Spice Model" → Extract MODEL VERSION PATH (relative path after PDK/)
- Use COMPLETE MODEL VERSION PATH: "tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"
- ❌ DO NOT use absolute paths: "/process/tsmcN5/data/g/PDK/tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"
- ❌ DO NOT use only version numbers: "spectre_v1d2_2p5"
- ✅ Use relative model path as shown in description example

**Check Behavior:**
Type 2 validates the extracted SPICE model version against the golden reference in pattern_items.
PASS if extracted `spice_model` matches `pattern_items[0]` (golden_spice).
FAIL if model version mismatch or extraction fails.

**Sample Output (PASS):**
```
Status: PASS
Reason: SPICE model version matched and validated against golden reference
INFO01:
  - SPICE Model: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs (Expected: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-13:
  description: "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
  requirements:
    value: 1
    pattern_items:
      - "tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\command_list.btxt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: SPICE model version check is informational - version mismatches are acceptable"
      - "Note: Legacy SPICE models are approved for use in this design phase"
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
  - "Explanation: SPICE model version check is informational - version mismatches are acceptable"
  - "Note: Legacy SPICE models are approved for use in this design phase"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - SPICE Model Mismatch: Found=tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs, Expected=tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-13:
  description: "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
  requirements:
    value: 1
    pattern_items:
      - "tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"  # Golden SPICE model version
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\command_list.btxt"
  waivers:
    value: 2
    waive_items:
      - name: "tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs"  # Legacy model version
        reason: "Waived - legacy SPICE model approved for this design per foundry team"
      - name: "tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"  # Alternative model
        reason: "Waived - alternative SPICE model validated for PGV in this technology node"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must use COMPLETE MODEL VERSION PATH format
- pattern_items: ["tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs"] (golden reference)
- waive_items.name: "tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs" (same format as pattern_items)
- ❌ DO NOT mix formats: pattern_items="tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs" with waive_items.name="spectre_v1d1_2p5"

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Validates SPICE model version against golden reference, with waiver classification:
- If extracted model matches golden reference → PASS (INFO01)
- If mismatch found and matches waive_items → PASS with [WAIVER] tag (INFO01)
- If mismatch found and NOT in waive_items → FAIL (ERROR01)
- Unused waivers → WARN with [WAIVER] tag
PASS if model matches golden OR all mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - SPICE Model: tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs (Expected: tsmc5g.a.12/models/spectre_v1d2_2p5/ir_em.scs) [WAIVER]
WARN01 (Unused Waivers):
  - tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs: Waiver not matched - no corresponding SPICE model version mismatch found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-13:
  description: "List Spice Model used for PGV generation. eg: tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\command_list.btxt"
  waivers:
    value: 2
    waive_items:
      - name: "tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs"  # Legacy model version
        reason: "Waived - legacy SPICE model approved for this design per foundry team"
      - name: "tsmc3gp.a.4/models/spectre_v1d0_2p6/ir_em.scs"  # Alternative model
        reason: "Waived - alternative SPICE model validated for PGV in this technology node"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Boolean check for SPICE model path existence, with waiver classification:
- If model path found → PASS (INFO01)
- If model path not found and matches waive_items → PASS with [WAIVER] tag (INFO01)
- If model path not found and NOT in waive_items → FAIL (ERROR01)
- Unused waivers → WARN with [WAIVER] tag
PASS if model exists OR all missing models are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - SPICE Model: tsmc5g.a.11/models/spectre_v1d1_2p5/ir_em.scs [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-13 --force

# Run individual tests
python IMP-2-0-0-13.py
```

---

## Notes

**Implementation Notes:**
- The checker extracts SPICE model paths from `spice_models` commands in command_list.btxt
- Model version is derived by extracting the relative path after "PDK/" directory
- For Type 1/4: Reports any SPICE model found (informational listing)
- For Type 2/3: Validates against golden model version in pattern_items[0]
- Output format includes both actual and expected model versions for Type 2/3

**Limitations:**
- Assumes SPICE model paths follow standard PDK directory structure with "PDK/" marker
- Only validates the first pattern_item as golden reference (single model version check)
- File analysis failed due to authentication issues - examples use typical SPICE model path formats

**Known Issues:**
- Input file analysis unavailable due to JEDAI authentication failure
- Pattern examples based on description and user hints rather than actual file content
- Regex patterns may need adjustment based on actual command_list.btxt format