# IMP-8-0-0-13: Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field.

## Overview

**Check ID:** IMP-8-0-0-13  
**Description:** Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field.  
**Category:** Clock Tree Synthesis (CTS) Library Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt`

This checker validates that the clock tree synthesis uses only approved cell types from the CTS library specification. It parses the allowed cell list containing clock buffers (DCCKND*), clock inverters (CKND2D*), clock gates (CKL*QD*), and clock logic cells (CKAN2D*, CKMUX2D*, etc.), categorizes them by function and drive strength, and provides a comprehensive inventory of permitted CTS cells for design verification.

---

## Check Logic

### Input Parsing
The checker parses the CTS cell library specification file line-by-line, tokenizing each line by whitespace to extract individual cell names. Multiple cells may appear on a single line. The parser categorizes cells into four main types: clock buffers, clock inverters, clock gates, and clock logic cells, extracting drive strength indicators and technology library identifiers.

**Key Patterns:**
```python
# Pattern 1: Clock tree buffer cells (DCCKND series)
pattern_buffer = r'(DCCKND(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'
# Example: "DCCKND4BWP300H8P64PDULVT DCCKND6BWP300H8P64PDULVT DCCKND8BWP300H8P64PDULVT"

# Pattern 2: Clock inverter cells (CKND2D series)
pattern_inverter = r'(CKND2D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'
# Example: "CKND2D2BWP300H8P64PDULVT CKND2D4BWP300H8P64PDULVT CKND2D8BWP300H8P64PDULVT"

# Pattern 3: Clock gate cells (CKL*QD pattern with wildcards)
pattern_clockgate = r'(CKL\*QD(\d+)\*H\d+\*[UL]LVT)'
# Example: "CKL*QD4*H8*ULVT CKL*QD6*H8*ULVT CKL*QD10*H8*ULVT"

# Pattern 4: Clock logic cells (CKAN2D, CKMUX2D, CKXOR2D, CKOR2D, CKNR2D)
pattern_logic = r'(CK(AN2|MUX2|XOR2|OR2|NR2)D(\d+)BWP\d+H\d+P\d+PD[UL]LVT)'
# Example: "CKAN2D2BWP300H8P64PDULVT CKMUX2D4BWP300H8P64PDULVT CKXOR2D8BWP300H8P64PDULVT"
```

### Detection Logic
1. **File Reading**: Read the CTS library specification file line-by-line
2. **Tokenization**: Split each line by whitespace to extract individual cell names
3. **Pattern Matching**: Apply regex patterns to identify and categorize each cell:
   - Match against buffer pattern (DCCKND*) → extract drive strength
   - Match against inverter pattern (CKND2D*) → extract drive strength
   - Match against clock gate pattern (CKL*QD*) → preserve wildcards, extract drive strength
   - Match against logic cell patterns (CKAN2D*, CKMUX2D*, etc.) → extract logic type and drive strength
4. **Categorization**: Group cells by category (buffer/inverter/gate/logic) and drive strength
5. **Aggregation**: If multiple files provided, merge all cell lists and remove duplicates
6. **Validation**: Check for empty file or non-standard cell types
7. **Output Generation**: Format cell inventory with category labels and drive strength indicators

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

**Rationale:** This checker validates that required CTS cell types exist in the library specification. The pattern_items represent mandatory cell categories (buffers, inverters, gates, logic) that SHOULD be present in the allowed cell list. The checker searches for these cell patterns in the input file and reports which ones are found versus missing.

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
item_desc = "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All required CTS cell types found in library specification"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required CTS cell patterns matched in library specification"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "CTS library specification contains all required clock tree cell types (buffers, inverters, gates, logic cells)"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All required CTS cell patterns matched and validated in library specification"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Required CTS cell types not found in library specification"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required CTS cell patterns not satisfied in library specification"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "CTS library specification missing required clock tree cell types"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required CTS cell patterns not satisfied or missing from library specification"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Missing CTS cell types waived per design team approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "CTS cell type absence waived - alternative cells approved by design team"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused CTS cell waiver entries"
unused_waiver_reason = "Waiver not matched - CTS cell type found in library specification (no violation)"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[CELL_NAME] - Drive: D[STRENGTH] (Category: [BUFFER|INVERTER|GATE|LOGIC])"
  Example: "DCCKND4BWP300H8P64PDULVT - Drive: D4 (Category: BUFFER)"
  Example: "CKND2D8BWP300H8P64PDULVT - Drive: D8 (Category: INVERTER)"
  Example: "CKL*QD6*H8*ULVT - Drive: D6 (Category: GATE)"
  Example: "CKMUX2D4BWP300H8P64PDULVT - Drive: D4 (Category: LOGIC-MUX2)"

ERROR01 (Violation/Fail items):
  Format: "[CELL_NAME] - Reason: [VIOLATION_REASON] (Line: [LINE_NUM])"
  Example: "BUFFD2BWP - Reason: Non-CTS buffer type used in clock tree (Line: 5)"
  Example: "INVD4BWP - Reason: Standard inverter not allowed in CTS library (Line: 12)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-13:
  description: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of the CTS library specification file. It checks if the file exists, is non-empty, and contains valid CTS cell definitions. PASS if file is valid and contains recognized CTS cell patterns. FAIL if file is missing, empty, or contains only invalid/non-standard cell types.

**Sample Output (PASS):**
```
Status: PASS
Reason: CTS library specification contains all required clock tree cell types (buffers, inverters, gates, logic cells)
INFO01:
  - DCCKND4BWP300H8P64PDULVT - Drive: D4 (Category: BUFFER)
  - DCCKND6BWP300H8P64PDULVT - Drive: D6 (Category: BUFFER)
  - DCCKND8BWP300H8P64PDULVT - Drive: D8 (Category: BUFFER)
  - CKND2D2BWP300H8P64PDULVT - Drive: D2 (Category: INVERTER)
  - CKND2D4BWP300H8P64PDULVT - Drive: D4 (Category: INVERTER)
  - CKL*QD4*H8*ULVT - Drive: D4 (Category: GATE)
  - CKL*QD6*H8*ULVT - Drive: D6 (Category: GATE)
  - CKAN2D2BWP300H8P64PDULVT - Drive: D2 (Category: LOGIC-AN2)
  - CKMUX2D4BWP300H8P64PDULVT - Drive: D4 (Category: LOGIC-MUX2)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: CTS library specification missing required clock tree cell types
ERROR01:
  - BUFFD2BWP - Reason: Non-CTS buffer type used in clock tree (Line: 5)
  - INVD4BWP - Reason: Standard inverter not allowed in CTS library (Line: 12)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-13:
  description: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - CTS cell inventory for design reference"
      - "Note: Non-standard cells are acceptable for this legacy design using custom CTS flow"
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
  - Explanation: This check is informational only - CTS cell inventory for design reference
  - Note: Non-standard cells are acceptable for this legacy design using custom CTS flow
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - BUFFD2BWP - Reason: Non-CTS buffer type used in clock tree (Line: 5) [WAIVED_AS_INFO]
  - INVD4BWP - Reason: Standard inverter not allowed in CTS library (Line: 12) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-13:
  description: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
  requirements:
    value: 3
    pattern_items:
      - "DCCKND4BWP300H8P64PDULVT"
      - "CKND2D4BWP300H8P64PDULVT"
      - "CKL*QD4*H8*ULVT"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches for specific CTS cell patterns in the library specification file. This is a requirement check where pattern_items represent mandatory CTS cells that MUST exist in the allowed cell list. PASS if all pattern_items are found (missing_items empty). FAIL if any required cells are not found in the specification.

**Sample Output (PASS):**
```
Status: PASS
Reason: All required CTS cell patterns matched and validated in library specification
INFO01:
  - DCCKND4BWP300H8P64PDULVT - Drive: D4 (Category: BUFFER)
  - CKND2D4BWP300H8P64PDULVT - Drive: D4 (Category: INVERTER)
  - CKL*QD4*H8*ULVT - Drive: D4 (Category: GATE)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-13:
  description: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
  requirements:
    value: 0
    pattern_items:
      - "DCCKND4BWP300H8P64PDULVT"
      - "CKND2D4BWP300H8P64PDULVT"
      - "CKL*QD4*H8*ULVT"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - CTS cell pattern verification for reference"
      - "Note: Missing cells are expected in minimal CTS library configuration for this block"
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
  - Explanation: This check is informational only - CTS cell pattern verification for reference
  - Note: Missing cells are expected in minimal CTS library configuration for this block
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - DCCKND4BWP300H8P64PDULVT - Reason: Required CTS buffer not found in library specification [WAIVED_AS_INFO]
  - CKL*QD4*H8*ULVT - Reason: Required clock gate pattern not found in library specification [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-13:
  description: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
  requirements:
    value: 3
    pattern_items:
      - "DCCKND4BWP300H8P64PDULVT"
      - "CKND2D4BWP300H8P64PDULVT"
      - "CKL*QD4*H8*ULVT"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "DCCKND4BWP300H8P64PDULVT"
        reason: "Waived - alternative buffer DCCKND6BWP300H8P64PDULVT approved for this design"
      - name: "CKL*QD4*H8*ULVT"
        reason: "Waived - clock gating disabled for this low-power block per design review"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2 (searches for required CTS cells), plus waiver classification:
- Match missing_items (required cells not found) against waive_items
- Unwaived missing cells → ERROR (need fix)
- Waived missing cells → INFO with [WAIVER] tag (approved exceptions)
- Unused waivers → WARN with [WAIVER] tag
PASS if all missing_items (required cells not found) are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All missing CTS cells waived per design team approval
INFO01 (Waived):
  - DCCKND4BWP300H8P64PDULVT - Reason: Waived - alternative buffer DCCKND6BWP300H8P64PDULVT approved for this design [WAIVER]
  - CKL*QD4*H8*ULVT - Reason: Waived - clock gating disabled for this low-power block per design review [WAIVER]
WARN01 (Unused Waivers):
  - No unused waivers
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-13:
  description: "Confirm proper clock tree buffer/inverter types are used. Provide a list in comment field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.0/IMP-8-0-0-13.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "DCCKND4BWP300H8P64PDULVT"
        reason: "Waived - alternative buffer DCCKND6BWP300H8P64PDULVT approved for this design"
      - name: "CKL*QD4*H8*ULVT"
        reason: "Waived - clock gating disabled for this low-power block per design review"
```

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (validates CTS library file), plus waiver classification:
- Match violations (invalid/missing cells) against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All missing CTS cells waived per design team approval
INFO01 (Waived):
  - DCCKND4BWP300H8P64PDULVT - Reason: Waived - alternative buffer DCCKND6BWP300H8P64PDULVT approved for this design [WAIVER]
  - CKL*QD4*H8*ULVT - Reason: Waived - clock gating disabled for this low-power block per design review [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-13 --force

# Run individual tests
python IMP-8-0-0-13.py
```

---

## Notes

- **Wildcard Handling**: Clock gate patterns with wildcards (e.g., `CKL*QD4*H8*ULVT`) are preserved as-is in the output. The checker does not expand wildcards but validates their presence in the specification.
- **Drive Strength Extraction**: Drive strength is extracted from cell names (D2, D4, D6, D8, D10, D12, D14) and displayed in the output for easy reference.
- **Multi-file Aggregation**: If multiple CTS library files are provided, the checker aggregates all cell definitions and removes duplicates before validation.
- **Technology Library**: All cells are expected to follow the naming convention with technology library identifier (e.g., `BWP300H8P64PDULVT` or `BWP300H8P64PDLLVT`).
- **Empty File Handling**: If the input file is empty or contains no valid CTS cell definitions, the checker returns FAIL with appropriate error message.
- **Line Number Tracking**: For invalid cell types, the checker reports the line number where the violation was detected for easy debugging.