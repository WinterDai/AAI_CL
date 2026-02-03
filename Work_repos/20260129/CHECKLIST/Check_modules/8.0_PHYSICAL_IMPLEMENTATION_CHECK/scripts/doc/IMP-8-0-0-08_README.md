# IMP-8-0-0-08: Confirm max routing layer is correct. Provide max routing layer value in comment field.

## Overview

**Check ID:** IMP-8-0-0-08  
**Description:** Confirm max routing layer is correct. Provide max routing layer value in comment field.  
**Category:** Physical Implementation - Routing Configuration Validation  
**Input Files:** C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt

This checker validates the maximum routing layer configuration by comparing the highest metal layers defined in three lists: techLayerList (available technology layers), SignalNetLayerList (signal routing layers), and PGNetLayerList (power/ground routing layers). It ensures that the routing configuration follows the hierarchy: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max. The checker extracts metal layer numbers (M0, M1, M2, etc.), ignores non-standard layers (like AP), and reports the maximum layer from each list.

---

## Check Logic

### Input Parsing
The checker parses a routing configuration file containing three key layer lists:

**Key Patterns:**
```python
# Pattern 1: Extract technology layer list (all available metal layers)
pattern_tech = r'^techLayerList:\s*(.+)$'
# Example: "techLayerList: M0 M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 AP"

# Pattern 2: Extract signal net routing layers
pattern_signal = r'^SignalNetLayerList:\s*(.+?)(?:#.*)?$'
# Example: "SignalNetLayerList: M9 M7 M5 M2 M3 M4 M6 M10 M1 M8 M11 M12"

# Pattern 3: Extract power/ground net routing layers
pattern_pg = r'^PGNetLayerList:\s*(.+?)(?:#.*)?$'
# Example: "PGNetLayerList: M7 M1 M2 M4 M6 M8 M10 M12 M0 M3 M5 M9 M11 M13  # Limit to 10KB"

# Pattern 4: Extract numeric value from metal layer name
pattern_metal = r'M(\d+)'
# Example: "M12" extracts "12", "M13" extracts "13"
```

### Detection Logic

1. **Parse Layer Lists:**
   - Read file line by line
   - Match lines against techLayerList, SignalNetLayerList, and PGNetLayerList patterns
   - Strip inline comments (anything after #)
   - Split layer strings on whitespace to get individual layer names

2. **Extract Metal Layers:**
   - For each layer list, filter only metal layers matching pattern M\d+ (M0, M1, M2, etc.)
   - Ignore non-standard layers (AP, VIA layers, etc.)
   - Extract numeric portion from each metal layer name

3. **Find Maximum Layers:**
   - techLayerList max: Highest M\d+ number in technology layer list
   - SignalNetLayerList max: Highest M\d+ number in signal routing layers
   - PGNetLayerList max: Highest M\d+ number in power/ground routing layers

4. **Validate Hierarchy:**
   - Check: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max
   - PASS: Hierarchy is correct
   - FAIL: Hierarchy is violated

5. **Requirements Validation (Type 2/3):**
   - If pattern_items specified: Check that pattern_items value ≤ techLayerList max
   - ERROR: If pattern_items value > techLayerList max (invalid configuration)
   - For Type 3: Check pattern_items value ≥ PGNetLayerList max ≥ SignalNetLayerList max
   - PASS: Requirements satisfied
   - ERROR: Requirements not satisfied

6. **Output:**
   - Print maximum layer from each list (e.g., "techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M13")
   - Report PASS/FAIL status based on hierarchy validation

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

Choose ONE mode based on what pattern_items represents:

### Mode 1: `existence_check` - Existence Check
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

### Mode 2: `status_check` - Status Check  
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

**Rationale:** This checker validates the maximum routing layer configuration against specified requirements. The pattern_items represent the expected maximum routing layer value (e.g., "M13"). The checker extracts the actual maximum layers from three lists and validates that the configuration hierarchy is correct. When pattern_items is specified, it defines the required maximum layer, and the checker verifies that this requirement is satisfied by comparing against the extracted PGNetLayerList and SignalNetLayerList maximums. This is a status validation (checking if the configuration meets the requirement), not an existence check.

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
item_desc = "Confirm max routing layer is correct. Provide max routing layer value in comment field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Max routing layer configuration validated"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Max routing layer requirement satisfied"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Routing layer hierarchy validated: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Required max routing layer matched and validated against configuration hierarchy"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Max routing layer configuration invalid"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Max routing layer requirement not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Routing layer hierarchy violation detected or configuration error"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required max routing layer not satisfied: pattern_items value exceeds techLayerList max or hierarchy violation"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Max routing layer configuration issue waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Routing layer configuration exception waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused routing layer waiver entry"
unused_waiver_reason = "Waiver entry not matched - no corresponding routing layer violation found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- Max routing layer: M13 (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M13): Routing layer hierarchy validated: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- Max routing layer: M14 (pattern_items exceeds techLayerList max M13): Required max routing layer not satisfied: pattern_items value exceeds techLayerList max or hierarchy violation"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-08:
  description: "Confirm max routing layer is correct. Provide max routing layer value in comment field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation of the routing layer hierarchy without requiring pattern_items. The checker extracts maximum metal layers from techLayerList, SignalNetLayerList, and PGNetLayerList, then validates the hierarchy: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max. PASS if hierarchy is correct, FAIL if violated.

**Sample Output (PASS):**
```
Status: PASS
Reason: Routing layer hierarchy validated: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max

Log format (CheckList.rpt):
INFO01:
  - Max routing layer: M13 (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M13)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: Max routing layer: M13 (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M13). In line 1, IMP-8-0-0-08.rpt: Routing layer hierarchy validated: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Routing layer hierarchy violation detected or configuration error

Log format (CheckList.rpt):
ERROR01:
  - Max routing layer hierarchy violation (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M16)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: Max routing layer hierarchy violation (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M16). In line 3, IMP-8-0-0-08.rpt: Routing layer hierarchy violation detected or configuration error
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-08:
  description: "Confirm max routing layer is correct. Provide max routing layer value in comment field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Routing layer hierarchy check is informational only for this design phase"
      - "Note: PGNetLayerList may exceed techLayerList during early floorplanning - will be corrected in final implementation"
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

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Routing layer hierarchy check is informational only for this design phase"
  - "Note: PGNetLayerList may exceed techLayerList during early floorplanning - will be corrected in final implementation"
INFO02:
  - Max routing layer hierarchy violation (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M16)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Routing layer hierarchy check is informational only for this design phase. [WAIVED_INFO]
2: Info: Note: PGNetLayerList may exceed techLayerList during early floorplanning - will be corrected in final implementation. [WAIVED_INFO]
3: Info: Max routing layer hierarchy violation (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M16). In line 3, IMP-8-0-0-08.rpt: Routing layer hierarchy violation detected or configuration error [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-08:
  description: "Confirm max routing layer is correct. Provide max routing layer value in comment field."
  requirements:
    value: 1  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "M13"  # ⚠️ MUST match description semantic level (metal layer identifier)
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "max routing layer" → Use METAL LAYER IDENTIFIERS (e.g., "M13", "M12")
  ❌ DO NOT use full descriptions: "Max routing layer: M13"
  ❌ DO NOT use numeric values only: "13"
- pattern_items value MUST NOT exceed techLayerList max (validated by checker)
- pattern_items value MUST be ≥ PGNetLayerList max ≥ SignalNetLayerList max for PASS

**Check Behavior:**
Type 2 validates that the specified pattern_items (required max routing layer) satisfies the configuration hierarchy. The checker:
1. Validates pattern_items value ≤ techLayerList max (ERROR if exceeded)
2. Checks pattern_items value ≥ PGNetLayerList max ≥ SignalNetLayerList max
3. PASS if requirements satisfied, ERROR if hierarchy violated

**Sample Output (PASS):**
```
Status: PASS
Reason: Required max routing layer matched and validated against configuration hierarchy

Log format (CheckList.rpt):
INFO01:
  - M13 (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M13)

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: M13 (techLayerList: M15, SignalNetLayerList: M12, PGNetLayerList: M13). In line 1, IMP-8-0-0-08.rpt: Required max routing layer matched and validated against configuration hierarchy
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required max routing layer not satisfied: pattern_items value exceeds techLayerList max or hierarchy violation

Log format (CheckList.rpt):
ERROR01:
  - M16 (pattern_items exceeds techLayerList max M15)

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: M16 (pattern_items exceeds techLayerList max M15). In line 1, IMP-8-0-0-08.rpt: Required max routing layer not satisfied: pattern_items value exceeds techLayerList max or hierarchy violation
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-8-0-0-08:
  description: "Confirm max routing layer is correct. Provide max routing layer value in comment field."
  requirements:
    value: 1
    pattern_items:
      - "M13"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Max routing layer requirement is informational only for this design phase"
      - "Note: Layer configuration will be finalized in detailed routing stage"
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

Log format (CheckList.rpt):
INFO01:
  - "Explanation: Max routing layer requirement is informational only for this design phase"
  - "Note: Layer configuration will be finalized in detailed routing stage"
INFO02:
  - M16 (pattern_items exceeds techLayerList max M15)

Report format (item_id.rpt):
Info Occurrence: 3
1: Info: Explanation: Max routing layer requirement is informational only for this design phase. [WAIVED_INFO]
2: Info: Note: Layer configuration will be finalized in detailed routing stage. [WAIVED_INFO]
3: Info: M16 (pattern_items exceeds techLayerList max M15). In line 1, IMP-8-0-0-08.rpt: Required max routing layer not satisfied: pattern_items value exceeds techLayerList max or hierarchy violation [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-08:
  description: "Confirm max routing layer is correct. Provide max routing layer value in comment field."
  requirements:
    value: 1  # ⚠️ CRITICAL: MUST equal len(pattern_items)
    pattern_items:
      - "M13"  # ⚠️ GOLDEN VALUE - Defines "what is correct"
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt
  waivers:
    value: 2
    waive_items:
      - name: "PGNetLayerList_M14"  # ⚠️ EXEMPTION - Defines "which exceptions are allowed"
        reason: "Power grid requires M14 for top-level routing - approved by design team"
      - name: "SignalNetLayerList_M14"
        reason: "Critical signal paths require M14 - timing closure exception"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern validation logic as Type 2, plus waiver classification:
- Match violations (hierarchy mismatches) against waive_items
- Unwaived violations → ERROR (need fix)
- Waived violations → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived

Log format (CheckList.rpt):
INFO01:
  - PGNetLayerList_M14 (hierarchy violation waived)
WARN01:
  - SignalNetLayerList_M14

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PGNetLayerList_M14 (hierarchy violation waived). In line 3, IMP-8-0-0-08.rpt: Routing layer configuration exception waived per design team approval: Power grid requires M14 for top-level routing - approved by design team [WAIVER]
Warn Occurrence: 1
1: Warn: SignalNetLayerList_M14. In line 0, IMP-8-0-0-08.rpt: Waiver entry not matched - no corresponding routing layer violation found: Critical signal paths require M14 - timing closure exception [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-8-0-0-08:
  description: "Confirm max routing layer is correct. Provide max routing layer value in comment field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - C:\Users\chyao\Desktop\checklist_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\8.0\IMP-8-0-0-08\IMP-8-0-0-08.rpt
  waivers:
    value: 2
    waive_items:
      - name: "PGNetLayerList_M14"  # ⚠️ MUST match Type 3 waive_items
        reason: "Power grid requires M14 for top-level routing - approved by design team"
      - name: "SignalNetLayerList_M14"
        reason: "Critical signal paths require M14 - timing closure exception"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean hierarchy check as Type 1 (no pattern_items), plus waiver classification:
- Match violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived

Log format (CheckList.rpt):
INFO01:
  - PGNetLayerList_M14 (hierarchy violation waived)
WARN01:
  - SignalNetLayerList_M14

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PGNetLayerList_M14 (hierarchy violation waived). In line 3, IMP-8-0-0-08.rpt: Routing layer configuration exception waived per design team approval: Power grid requires M14 for top-level routing - approved by design team [WAIVER]
Warn Occurrence: 1
1: Warn: SignalNetLayerList_M14. In line 0, IMP-8-0-0-08.rpt: Waiver entry not matched - no corresponding routing layer violation found: Critical signal paths require M14 - timing closure exception [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.0_PHYSICAL_IMPLEMENTATION_CHECK --checkers IMP-8-0-0-08 --force

# Run individual tests
python IMP-8-0-0-08.py
```

---

## Notes

**Implementation Notes:**
- The checker ignores non-standard layers (e.g., AP - antenna protection layer) when determining maximum metal layers
- Only layers matching the pattern M\d+ (M0, M1, M2, etc.) are considered for maximum layer calculation
- Inline comments in the configuration file (marked with #) are automatically stripped during parsing
- Empty or missing layer lists will trigger an ERROR condition

**Validation Rules:**
- techLayerList must be present and contain at least one metal layer
- At least one routing list (SignalNetLayerList or PGNetLayerList) must be present
- All layers in routing lists must exist in techLayerList (validated by checker)
- For Type 2/3: pattern_items value must not exceed the maximum layer number in techLayerList

**Known Limitations:**
- The checker assumes metal layers follow the naming convention M\d+ (M followed by digits)
- Non-standard layer naming schemes may not be properly detected
- The hierarchy validation is strict: SignalNetLayerList max ≤ PGNetLayerList max ≤ techLayerList max
- Duplicate layer names in the same list are acceptable (automatically deduplicated)

**Edge Cases:**
- If PGNetLayerList is empty but SignalNetLayerList has layers, the check may still PASS if hierarchy is maintained
- If both routing lists are empty, the checker will report an ERROR
- Whitespace and tab characters are normalized during parsing
- Case sensitivity: Layer names are case-sensitive (M12 vs m12 are different)