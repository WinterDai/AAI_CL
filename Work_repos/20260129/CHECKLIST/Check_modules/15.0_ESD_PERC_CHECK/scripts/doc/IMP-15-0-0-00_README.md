# IMP-15-0-0-00: Confirm whether ESD PERC check is needed.

## Overview

**Check ID:** IMP-15-0-0-00  
**Description:** Confirm whether ESD PERC check is needed.  
**Category:** ESD Verification  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt`

This checker verifies whether ESD (Electrostatic Discharge) PERC (Physical Extraction and Rule Check) validation is required for the design. It examines the ESD verification report to determine if ESD protection structures and rules have been properly checked. The checker validates that ESD PERC analysis has been performed when required by the design flow.

---

## Check Logic

### Input Parsing
The checker determines if ESD PERC check is needed based on the design type. The correct check logic is:
- **If design is phy_top OR tv_chip**: ESD PERC check is required (PASS)
- **Otherwise**: ESD PERC check is not required (FAIL)

**Key Patterns:**
```python
# Pattern 1: Design type identification - phy_top
pattern1 = r'design_type\s*:\s*\S*phy_top'
# Example: "design_type: phy_top" or "design_type: soc_phy_top"

# Pattern 2: Design type identification - tv_chip
pattern2 = r'design_type\s*:\s*tv_chip'
# Example: "design_type: tv_chip"

# Pattern 3: Alternative design type format
pattern3 = r'(phy_top|tv_chip)'
# Example: "Current design: phy_top" or "Chip type: tv_chip"
```

### Detection Logic
1. Check if the input report file exists
2. If file exists, parse for design type indicators (phy_top or tv_chip)
3. Determine if design matches phy_top or tv_chip criteria
4. Return PASS if design is phy_top OR tv_chip (ESD PERC check needed)
5. Return FAIL if design is neither phy_top nor tv_chip (ESD PERC check not needed)

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

**Rationale:** This checker validates the status of design type to determine if ESD PERC check is needed. It checks whether the design matches specific types (phy_top or tv_chip) that require ESD PERC verification, rather than simply checking for the existence of items. The checker needs to validate that the design type has been identified and matches the criteria for ESD PERC requirements.

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
item_desc = "Confirm whether ESD PERC check is needed."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Design type found - ESD PERC check is required"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Design type matched - ESD PERC check is required (phy_top or tv_chip)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Design type is phy_top or tv_chip - ESD PERC check required"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Design type matched phy_top or tv_chip criteria - ESD PERC check validated as required"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Design type not found or does not require ESD PERC check"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Design type does not match phy_top or tv_chip - ESD PERC check not required"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Design type is not phy_top or tv_chip - ESD PERC check not required"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Design type does not satisfy phy_top or tv_chip criteria - ESD PERC check not required"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "ESD PERC check requirements waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "ESD PERC requirement waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused ESD PERC waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding ESD PERC requirement found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Design type: [type] - ESD PERC check required"
  Example: "Design type: phy_top - ESD PERC check required"

ERROR01 (Violation/Fail items):
  Format: "Design type: [type] - ESD PERC check not required"
  Example: "Design type: digital_block - ESD PERC check not required"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-00:
  description: "Confirm whether ESD PERC check is needed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
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
Reason: Design type is phy_top or tv_chip - ESD PERC check required
INFO01:
  - Design type: phy_top - ESD PERC check required
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Design type is not phy_top or tv_chip - ESD PERC check not required
ERROR01:
  - Design type: digital_block - ESD PERC check not required
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-00:
  description: "Confirm whether ESD PERC check is needed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: ESD PERC check requirement is informational only for this design phase"
      - "Note: Design type verification will be performed in final tape-out stage"
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
  - "Explanation: ESD PERC check requirement is informational only for this design phase"
  - "Note: Design type verification will be performed in final tape-out stage"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Design type: digital_block - ESD PERC check not required [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-00:
  description: "Confirm whether ESD PERC check is needed."
  requirements:
    value: 2
    pattern_items:
      - "*phy_top"
      - "*tv_chip"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: Design type matched phy_top or tv_chip criteria - ESD PERC check validated as required
INFO01:
  - Design type: phy_top - ESD PERC check required
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-15-0-0-00:
  description: "Confirm whether ESD PERC check is needed."
  requirements:
    value: 0
    pattern_items:
      - "*phy_top"
      - "*tv_chip"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Design type validation is informational for early design stages"
      - "Note: Pattern mismatches are expected until final design type is confirmed"
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
  - "Explanation: Design type validation is informational for early design stages"
  - "Note: Pattern mismatches are expected until final design type is confirmed"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Design type: digital_block - Does not match phy_top or tv_chip [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-00:
  description: "Confirm whether ESD PERC check is needed."
  requirements:
    value: 2
    pattern_items:
      - "*phy_top"
      - "*tv_chip"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "*digital_block"
        reason: "Waived - Digital block design does not require ESD PERC check per design specification"
      - name: "*analog_block"
        reason: "Waived - Analog block uses custom ESD protection scheme"
```

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
INFO01 (Waived):
  - Design type: digital_block - Does not match phy_top or tv_chip [WAIVER]
WARN01 (Unused Waivers):
  - design_type: *analog_block: Waiver entry not matched - no corresponding ESD PERC requirement found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-15-0-0-00:
  description: "Confirm whether ESD PERC check is needed."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "*digital_block"
        reason: "Waived - Digital block design does not require ESD PERC check per design specification"
      - name: "*analog_block"
        reason: "Waived - Analog block uses custom ESD protection scheme"
```

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
INFO01 (Waived):
  - Design type: digital_block - Does not match phy_top or tv_chip [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 15.0_ESD_PERC_CHECK --checkers IMP-15-0-0-00 --force

# Run individual tests
python IMP-15-0-0-00.py
```

---

## Notes

- The input file `IMP-7-0-0-00.rpt` does not currently exist in the analysis environment
- This checker determines if ESD PERC check is needed based on design type: **phy_top OR tv_chip**
- **Correct logic**: If design is phy_top OR tv_chip → PASS (ESD PERC check required), otherwise → FAIL (not required)
- ESD PERC checks are typically required for physical top-level designs and TV chip designs
- For other design types (digital blocks, analog blocks, etc.), ESD PERC verification may not be necessary
- Waiver support (Type 3/4) allows documenting design types that don't require ESD PERC checks