# MIG-IMP-8-1-1-01: Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)

## Overview

**Check ID:** MIG-IMP-8-1-1-01  
**Description:** Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)  
**Category:** Physical Implementation - Parasitic RC Validation  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt`

This checker validates pad-to-bump parasitic RC (Resistance-Capacitance) values extracted at specific RC corners. It ensures that each signal net meets the design constraints:
- **Resistance**: Must be < 0.5Ω (hard limit), with warning threshold at 0.8Ω
- **Capacitance**: Must be < 350fF (hard limit)

The checker parses RC extraction reports containing per-net resistance and capacitance values, identifies violations, and reports nets that exceed the specified limits. This validation is critical for signal integrity and timing closure.

---

## Check Logic

### Input Parsing
The checker parses RC extraction reports with the following structure:
- Each net block starts with `Net: <net_name>`
- RC corner information: `RC Corner: <corner_name>`
- Total capacitance: `Total Cap = <value> ff`
- Total resistance: `Total Res = <value> ohms`

**Key Patterns:**
```python
# Pattern 1: Net name extraction
pattern_net = r'^Net:\s+([\w\[\]_]+)\s*$'
# Example: "Net: pad_mem_data[47]"

# Pattern 2: RC corner extraction
pattern_corner = r'^RC Corner:\s+(.+)\s*$'
# Example: "RC Corner: rcworst_CCworst_T_125c"

# Pattern 3: Total capacitance extraction
pattern_cap = r'^Total Cap\s*=\s*([\d.]+)\s*ff\s*$'
# Example: "Total Cap  = 291.239105 ff"

# Pattern 4: Total resistance extraction
pattern_res = r'^Total Res\s*=\s*([\d.]+)\s*ohms\s*$'
# Example: "Total Res  = 0.379863 ohms"
```

### Detection Logic
1. **Parse each net block** sequentially from the input report
2. **Extract values** for net_name, rc_corner, capacitance, and resistance
3. **Apply validation rules**:
   - **FAIL (ERROR)**: Resistance ≥ 0.5Ω OR Capacitance ≥ 350fF
   - **WARNING**: 0.5Ω ≤ Resistance < 0.8Ω (soft limit exceeded)
   - **PASS**: Resistance < 0.5Ω AND Capacitance < 350fF
4. **Aggregate results**:
   - Count total nets analyzed
   - Track pass/fail/warning counts per RC corner
   - Collect violation details for ERROR01 output
5. **Return status**:
   - PASS if all nets meet hard limits (R < 0.5Ω, C < 350fF)
   - FAIL if any net exceeds hard limits

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

**Rationale:** This checker validates the RC status of specific nets. When pattern_items are provided, it checks whether those nets meet the resistance/capacitance limits. Only nets matching pattern_items are evaluated and reported. Nets not in pattern_items are ignored even if they have violations. The check passes when all specified nets satisfy the RC constraints.

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
item_desc = "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "All nets found with RC values within limits"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All specified nets matched and satisfied RC constraints (R < 0.5Ω, C < 350fF)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "All analyzed nets found with resistance < 0.5Ω and capacitance < 350fF"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All specified nets matched and validated: resistance < 0.5Ω and capacitance < 350fF satisfied"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Nets not found or RC limits exceeded"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Specified nets not satisfied: RC constraints violated (R ≥ 0.5Ω or C ≥ 350fF)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "One or more nets not found or exceeded RC limits (R ≥ 0.5Ω or C ≥ 350fF)"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "One or more specified nets not satisfied: RC constraints failed (R ≥ 0.5Ω or C ≥ 350fF)"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "RC violations waived per design approval"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "RC violation waived: resistance or capacitance limit exceeded but approved by design team"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused RC waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding RC violation found for this net"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "[net_name] @ {rc_corner}: R={resistance}Ω, C={capacitance}fF - PASS"
  Example: "pad_mem_data[47] @ rcworst_CCworst_T_125c: R=0.379863Ω, C=291.239105fF - PASS"

ERROR01 (Violation/Fail items):
  Format: "[net_name] @ {rc_corner}: R={resistance}Ω (limit: 0.5Ω), C={capacitance}fF (limit: 350fF) - {violation_type}"
  Example: "pad_mem_data[12] @ rcworst_CCworst_T_125c: R=0.623Ω (limit: 0.5Ω), C=385.5fF (limit: 350fF) - RESISTANCE_VIOLATION, CAPACITANCE_VIOLATION"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-1-01:
  description: "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt"
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
Reason: All analyzed nets found with resistance < 0.5Ω and capacitance < 350fF
INFO01:
  - pad_mem_data[47] @ rcworst_CCworst_T_125c: R=0.379863Ω, C=291.239105fF - PASS
  - pad_mem_data[56] @ rcworst_CCworst_T_125c: R=0.381849Ω, C=313.009827fF - PASS
  - pad_mem_data[23] @ rcworst_CCworst_T_125c: R=0.238066Ω, C=235.482056fF - PASS
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: One or more nets not found or exceeded RC limits (R ≥ 0.5Ω or C ≥ 350fF)
ERROR01:
  - pad_mem_data[12] @ rcworst_CCworst_T_125c: R=0.623Ω (limit: 0.5Ω), C=385.5fF (limit: 350fF) - RESISTANCE_VIOLATION, CAPACITANCE_VIOLATION
  - pad_mem_clk @ rcworst_CCworst_T_125c: R=0.512Ω (limit: 0.5Ω), C=298.3fF (limit: 350fF) - RESISTANCE_VIOLATION
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
MIG-IMP-8-1-1-01:
  description: "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: RC violations are informational only for this design phase"
      - "Note: Violations will be addressed in final layout optimization"
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
  - Explanation: RC violations are informational only for this design phase
  - Note: Violations will be addressed in final layout optimization
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - pad_mem_data[12] @ rcworst_CCworst_T_125c: R=0.623Ω (limit: 0.5Ω), C=385.5fF (limit: 350fF) - RESISTANCE_VIOLATION, CAPACITANCE_VIOLATION [WAIVED_AS_INFO]
  - pad_mem_clk @ rcworst_CCworst_T_125c: R=0.512Ω (limit: 0.5Ω), C=298.3fF (limit: 350fF) - RESISTANCE_VIOLATION [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-1-01:
  description: "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "pad_mem_data[47]"
      - "pad_mem_data[56]"
      - "pad_mem_clk"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt"
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
Reason: All specified nets matched and validated: resistance < 0.5Ω and capacitance < 350fF satisfied
INFO01:
  - pad_mem_data[47] @ rcworst_CCworst_T_125c: R=0.379863Ω, C=291.239105fF - PASS
  - pad_mem_data[56] @ rcworst_CCworst_T_125c: R=0.381849Ω, C=313.009827fF - PASS
  - pad_mem_clk @ rcworst_CCworst_T_125c: R=0.238066Ω, C=235.482056fF - PASS
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
MIG-IMP-8-1-1-01:
  description: "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "pad_mem_data[47]"
      - "pad_mem_data[56]"
      - "pad_mem_clk"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: RC pattern check is informational only for early design phase"
      - "Note: Pattern mismatches are expected during initial layout and do not require immediate fixes"
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
  - Explanation: RC pattern check is informational only for early design phase
  - Note: Pattern mismatches are expected during initial layout and do not require immediate fixes
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - pad_mem_data[47] @ rcworst_CCworst_T_125c: R=0.623Ω (limit: 0.5Ω), C=385.5fF (limit: 350fF) - RESISTANCE_VIOLATION, CAPACITANCE_VIOLATION [WAIVED_AS_INFO]
  - pad_mem_clk @ rcworst_CCworst_T_125c: R=0.512Ω (limit: 0.5Ω), C=298.3fF (limit: 350fF) - RESISTANCE_VIOLATION [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-1-01:
  description: "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
  requirements:
    value: 3
    pattern_items:
      - "pad_mem_data[47]"
      - "pad_mem_data[56]"
      - "pad_mem_clk"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "pad_mem_data[12]"
        reason: "Waived per design review - non-critical debug signal, acceptable for this corner"
      - name: "pad_mem_clk"
        reason: "Waived - resistance margin acceptable, clock path has sufficient timing margin"
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
  - pad_mem_data[12] @ rcworst_CCworst_T_125c: R=0.623Ω (limit: 0.5Ω), C=385.5fF (limit: 350fF) - RESISTANCE_VIOLATION, CAPACITANCE_VIOLATION [WAIVER]
  - pad_mem_clk @ rcworst_CCworst_T_125c: R=0.512Ω (limit: 0.5Ω), C=298.3fF (limit: 350fF) - RESISTANCE_VIOLATION [WAIVER]
WARN01 (Unused Waivers):
  - pad_mem_data[99] @ rcworst_CCworst_T_125c: Waiver not matched - no corresponding RC violation found for this net
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
MIG-IMP-8-1-1-01:
  description: "Confirm meet a resistance less than 0.5Ω(not exceed 0.8Ω) and a capacitance less than 350fF from pad opening to signal bump. (check the Note)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/8.1/MIG-IMP-8-1-1-01.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "pad_mem_data[12]"
        reason: "Waived per design review - non-critical debug signal, acceptable for this corner"
      - name: "pad_mem_clk"
        reason: "Waived - resistance margin acceptable, clock path has sufficient timing margin"
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
  - pad_mem_data[12] @ rcworst_CCworst_T_125c: R=0.623Ω (limit: 0.5Ω), C=385.5fF (limit: 350fF) - RESISTANCE_VIOLATION, CAPACITANCE_VIOLATION [WAIVER]
  - pad_mem_clk @ rcworst_CCworst_T_125c: R=0.512Ω (limit: 0.5Ω), C=298.3fF (limit: 350fF) - RESISTANCE_VIOLATION [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 8.1_PHYSICAL_IMPLEMENTATION_CHECK --checkers MIG-IMP-8-1-1-01 --force

# Run individual tests
python MIG-IMP-8-1-1-01.py
```

---

## Notes

- **RC Corner Context**: All measurements are performed at specific RC corners (e.g., `rcworst_CCworst_T_125c`). The checker reports the corner name with each violation for proper context.
- **Resistance Limits**: 
  - Hard limit: 0.5Ω (FAIL if exceeded)
  - Soft limit: 0.8Ω (WARNING if exceeded but < 0.5Ω)
- **Capacitance Limit**: Hard limit at 350fF (FAIL if exceeded)
- **Multi-violation Reporting**: A single net can violate both resistance and capacitance limits simultaneously. The checker reports all applicable violations.
- **Net Naming**: Supports bus notation (e.g., `pad_mem_data[47]`) and standard signal names.
- **File Format**: The checker expects the standard RC extraction report format with consistent section delimiters (`Net:`, `RC Corner:`, `Total Cap`, `Total Res`).
- **Performance**: For large designs with thousands of nets, the checker processes sequentially and may take several seconds to complete.