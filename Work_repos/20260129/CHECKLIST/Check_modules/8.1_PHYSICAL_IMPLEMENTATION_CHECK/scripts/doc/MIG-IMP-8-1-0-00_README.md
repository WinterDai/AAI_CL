# MIG-IMP-8-1-0-00: Confirm followed the general slice top metal and top routing layer spec. (check the Note)

## Overview

**Check ID:** MIG-IMP-8-1-0-00  
**Description:** Confirm followed the general slice top metal and top routing layer spec. (check the Note)  
**Category:** Physical Implementation - Routing Layer Configuration  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt`

This checker validates that the routing layer configuration follows the general slice top metal and top routing layer specifications. It verifies that the top routing layer for signal nets is within an acceptable range of the top metal layer (typically within 1-2 layers). The checker parses the technology layer list and signal net routing layer list to identify the highest metal layers and compares them against design specifications.

---

## Check Logic

### Input Parsing

The checker parses the routing layer configuration report to extract:
1. **Technology Layer List** (`techLayerList`): All available metal layers in the technology
2. **Signal Net Routing Layer List** (`SignalNetLayerList`): Routing layers available for signal nets
3. **Power/Ground Net Routing Layer List** (`PGNetLayerList`): Routing layers for PG nets (informational)

**Key Patterns:**
```python
# Pattern 1: Technology layer list - defines all available metal layers
pattern_tech_layers = r'^techLayerList:\s*(.+)$'
# Example: "techLayerList: M0 M1 M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 M13 M14 M15 AP"

# Pattern 2: Signal net routing layer list - defines routing layers for signal nets
pattern_signal_layers = r'^SignalNetLayerList:\s*(.+?)(?:\s*#.*)?$'
# Example: "SignalNetLayerList: M9 M7 M5 M2 M3 M4 M6 M10 M1 M8 M11 M12"

# Pattern 3: Power/Ground net routing layer list
pattern_pg_layers = r'^PGNetLayerList:\s*(.+?)(?:\s*#.*)?$'
# Example: "PGNetLayerList: M7 M1 M2 M4 M6 M8 M10 M12 M0 M3 M5 M9 M11 M13  # Limit to 10KB"

# Pattern 4: Metal layer number extraction for comparison
pattern_metal_number = r'M(\d+)'
# Example: "M15" -> extracts 15, "M12" -> extracts 12
```

### Detection Logic

1. **Parse Technology Layers:**
   - Extract all layers from `techLayerList`
   - Filter metal layers (M followed by number)
   - Exclude special layers (AP, etc.)
   - Identify top metal layer (highest M-number)

2. **Parse Signal Routing Layers:**
   - Extract all layers from `SignalNetLayerList`
   - Filter metal layers
   - Identify top signal routing layer (highest M-number in the list)

3. **Validate Layer Specification:**
   - Compare top signal routing layer against top metal layer
   - Apply specification rule: top_routing should be within 1-2 layers of top_metal
   - Common spec: `top_metal - 2 <= top_routing <= top_metal`

4. **Generate Results:**
   - **PASS:** Top routing layer meets specification (within acceptable range)
   - **FAIL:** Top routing layer violates specification (too far from top metal)
   - Report summary statistics: layer counts, top layers identified

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

**Rationale:** This checker validates the status/compliance of routing layer configuration against specifications. It checks whether the top routing layer configuration meets the required relationship with the top metal layer (within acceptable range). The checker examines specific layer configurations and validates their correctness, rather than simply checking for existence of items.

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
item_desc = "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Routing layer configuration found and validated"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Top routing layer specification satisfied - within acceptable range of top metal layer"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Routing layer configuration found and top routing layer is within specification"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Top routing layer specification matched and validated - routing layer within acceptable range of top metal"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Routing layer configuration not found or incomplete"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Top routing layer specification not satisfied - routing layer outside acceptable range"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required routing layer configuration not found in report file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Top routing layer specification not satisfied - routing layer exceeds acceptable distance from top metal layer"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Waived routing layer specification violations"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Routing layer configuration violation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for routing layer checks"
unused_waiver_reason = "Waiver not matched - no corresponding routing layer violation found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Top Metal: [layer], Top Signal Routing: [layer], Distance: [N] layers - COMPLIANT"
  Example: "Top Metal: M15, Top Signal Routing: M12, Distance: 3 layers - COMPLIANT (within spec: top_metal-2 to top_metal)"

ERROR01 (Violation/Fail items):
  Format: "ROUTING LAYER VIOLATION: Top Metal: [layer], Top Signal Routing: [layer], Distance: [N] layers - EXCEEDS SPEC"
  Example: "ROUTING LAYER VIOLATION: Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC (allowed: top_metal-2 to top_metal)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-0-00:
  description: "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt"
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
Reason: Routing layer configuration found and top routing layer is within specification
INFO01:
  - Top Metal: M15, Top Signal Routing: M12, Distance: 3 layers - COMPLIANT (within spec: top_metal-2 to top_metal)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required routing layer configuration not found in report file
ERROR01:
  - ROUTING LAYER VIOLATION: techLayerList not found in report file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
MIG-IMP-8-1-0-00:
  description: "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only for legacy designs using non-standard routing layer configurations"
      - "Note: Routing layer violations are expected in designs with custom metal stack definitions and do not require fixes"
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
  - "Explanation: This check is informational only for legacy designs using non-standard routing layer configurations"
  - "Note: Routing layer violations are expected in designs with custom metal stack definitions and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ROUTING LAYER VIOLATION: Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-0-00:
  description: "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "Top Metal: M15, Top Signal Routing: M12"
      - "Top Metal: M15, Top Signal Routing: M13"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt"
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
Reason: Top routing layer specification matched and validated - routing layer within acceptable range of top metal
INFO01:
  - Top Metal: M15, Top Signal Routing: M12, Distance: 3 layers - COMPLIANT
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
MIG-IMP-8-1-0-00:
  description: "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "Top Metal: M15, Top Signal Routing: M12"
      - "Top Metal: M15, Top Signal Routing: M13"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only for designs with approved custom routing layer configurations"
      - "Note: Pattern mismatches are expected in designs using alternative metal stack strategies and do not require fixes"
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
  - "Explanation: This check is informational only for designs with approved custom routing layer configurations"
  - "Note: Pattern mismatches are expected in designs using alternative metal stack strategies and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - ROUTING LAYER VIOLATION: Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-0-00:
  description: "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
  requirements:
    value: 2
    pattern_items:
      - "Top Metal: M15, Top Signal Routing: M12"
      - "Top Metal: M15, Top Signal Routing: M13"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC"
        reason: "Waived per design review - custom metal stack approved for low-power optimization"
      - name: "Top Metal: M15, Top Signal Routing: M9, Distance: 6 layers - EXCEEDS SPEC"
        reason: "Waived - legacy design constraint, acceptable for this IP block"
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
  - Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC [WAIVER]
WARN01 (Unused Waivers):
  - Top Metal: M15, Top Signal Routing: M9, Distance: 6 layers - EXCEEDS SPEC: Waiver not matched - no corresponding routing layer violation found
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-0-00:
  description: "Confirm followed the general slice top metal and top routing layer spec. (check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/IMP-8-0-0-08.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC"
        reason: "Waived per design review - custom metal stack approved for low-power optimization"
      - name: "Top Metal: M15, Top Signal Routing: M9, Distance: 6 layers - EXCEEDS SPEC"
        reason: "Waived - legacy design constraint, acceptable for this IP block"
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
  - Top Metal: M15, Top Signal Routing: M10, Distance: 5 layers - EXCEEDS SPEC [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.1_PHYSICAL_IMPLEMENTATION_CHECK --checkers MIG-IMP-8-1-0-00 --force

# Run individual tests
python MIG-IMP-8-1-0-00.py
```

---

## Notes

**Specification Assumptions:**
- Default specification: Top routing layer should be within 2 layers of top metal layer
- Formula: `top_metal - 2 <= top_routing <= top_metal`
- Common acceptable configurations:
  - Top routing = Top metal (M15 routing on M15 metal)
  - Top routing = Top metal - 1 (M14 routing on M15 metal)
  - Top routing = Top metal - 2 (M13 routing on M15 metal)

**Edge Cases Handled:**
- Missing `techLayerList` → Report ERROR, cannot determine top metal
- Missing `SignalNetLayerList` → Report ERROR, cannot determine top routing
- Empty layer lists → Report ERROR
- Non-standard layer naming (not M followed by number) → Filtered out, may trigger WARNING
- Special layers (AP, etc.) → Excluded from metal layer numbering
- Multiple occurrences of same list type → Uses last occurrence

**Known Limitations:**
- Checker assumes standard metal layer naming convention (M0, M1, M2, etc.)
- Specification threshold (2 layers) may need to be configurable for different technologies
- Does not validate PGNetLayerList compliance (informational only)

**File Format:**
The input report file contains three main lines:
1. `techLayerList:` - Space-separated list of all technology layers
2. `SignalNetLayerList:` - Space-separated list of routing layers for signal nets
3. `PGNetLayerList:` - Space-separated list of routing layers for power/ground nets (may include comments)