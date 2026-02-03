# IMP-12-0-0-05: Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck.

## Overview

**Check ID:** IMP-12-0-0-05  
**Description:** Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck.  
**Category:** Physical Verification - DRC Configuration  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log` (Pegasus DRC log)
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme` (Calibre DRC configuration)

This checker validates that the IP_TIGHTEN_DENSITY directive is enabled (uncommented) in the DRC rule deck configuration file. The IP_TIGHTEN_DENSITY switch controls local density checking at IP/macro/block level, which is critical for ensuring proper metal density distribution in physical verification. The checker supports both Calibre (do_cmd_3star_DRC_sourceme) and Pegasus (do_pvs_DRC_pvl.log) DRC configurations, requiring only one file to be specified.

---

## Check Logic

### Input Parsing

The checker parses DRC configuration files to locate and validate the IP_TIGHTEN_DENSITY switch status. It supports two file types:

1. **Calibre DRC Configuration** (`do_cmd_3star_DRC_sourceme`):
   - Line-by-line parsing of #DEFINE directives
   - Tracks enabled (uncommented) vs disabled (commented) switches
   - Extracts inline comments for context

2. **Pegasus DRC Log** (`do_pvs_DRC_pvl.log`):
   - Similar parsing strategy for Pegasus-specific syntax
   - Validates switch configuration in log output

**Key Patterns:**

```python
# Pattern 1: Enabled IP_TIGHTEN_DENSITY switch (active #DEFINE)
pattern_enabled = r'^\s*#DEFINE\s+IP_TIGHTEN_DENSITY\s*(?://.*)?$'
# Example: "#DEFINE IP_TIGHTEN_DENSITY       // Turn on to tighten local density check in IP/macro/block level"

# Pattern 2: Disabled/commented IP_TIGHTEN_DENSITY switch (inactive)
pattern_disabled = r'^\s*(?://|#)\s*#?DEFINE\s+IP_TIGHTEN_DENSITY\s*(?://.*)?$'
# Example: "//#DEFINE IP_TIGHTEN_DENSITY       // Turn on to tighten local density check in IP/macro/block level"

# Pattern 3: Any #DEFINE directive (for context validation)
pattern_any_define = r'^\s*#DEFINE\s+(\w+)\s*(?://(.*))?$'
# Example: "#DEFINE CHECK_HIGH_DENSITY  // Turn off to skip local high density rule checks in cell level"

# Pattern 4: Commented #DEFINE directive (disabled switches)
pattern_commented_define = r'^\s*//\s*#DEFINE\s+(\w+)\s*(?://(.*))?$'
# Example: "//#DEFINE FULL_CHIP           // Turn on for chip level design"
```

### Detection Logic

1. **File Selection**: Check which input file exists (either Calibre or Pegasus)
2. **Line-by-Line Parsing**: 
   - Read configuration file sequentially with line number tracking
   - Track current section context from comment headers
   - Match each line against #DEFINE patterns
3. **Switch Detection**:
   - Search specifically for IP_TIGHTEN_DENSITY directive
   - Determine state: ENABLED (uncommented #DEFINE), DISABLED (commented //), or MISSING (not found)
   - Record line number and inline comment for reporting
4. **Validation**:
   - PASS: IP_TIGHTEN_DENSITY is ENABLED (uncommented #DEFINE found)
   - FAIL: IP_TIGHTEN_DENSITY is DISABLED (commented out) or MISSING (not found in file)
5. **Edge Cases**:
   - Multiple occurrences: Last occurrence determines final state
   - Extra whitespace/tabs: Pattern handles flexible spacing
   - Inline comments: Extracted for context
   - Empty file or missing file: Caught by validate_input_files

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

**Rationale:** This checker validates the STATUS of the IP_TIGHTEN_DENSITY directive (ENABLED vs DISABLED). The pattern_items contain directive names to search for, and the checker validates that each directive is in the correct state (uncommented/enabled). Only directives listed in pattern_items are checked, and the output reports whether each directive has the correct status (enabled) or incorrect status (disabled/missing).

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
item_desc = "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "IP_TIGHTEN_DENSITY switch found and enabled in DRC configuration"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "IP_TIGHTEN_DENSITY directive validated as enabled"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "IP_TIGHTEN_DENSITY switch found and enabled in DRC rule deck configuration"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "IP_TIGHTEN_DENSITY directive matched and validated as enabled in DRC configuration"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "IP_TIGHTEN_DENSITY switch not enabled in DRC configuration"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "IP_TIGHTEN_DENSITY directive not satisfied (disabled or missing)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "IP_TIGHTEN_DENSITY switch not found or disabled in DRC rule deck - must be uncommented"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "IP_TIGHTEN_DENSITY directive not satisfied - switch is commented out or missing from configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "IP_TIGHTEN_DENSITY switch requirement waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "IP_TIGHTEN_DENSITY switch requirement waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for IP_TIGHTEN_DENSITY check"
unused_waiver_reason = "Waiver not matched - IP_TIGHTEN_DENSITY directive not found in specified state"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Switch: IP_TIGHTEN_DENSITY | Status: ENABLED | File: <path> | Line: <number>"
  Example: "Switch: IP_TIGHTEN_DENSITY | Status: ENABLED | File: do_cmd_3star_DRC_sourceme | Line: 42"

ERROR01 (Violation/Fail items):
  Format: "Switch: IP_TIGHTEN_DENSITY | Status: DISABLED/MISSING | File: <path> | Recommendation: Uncomment #DEFINE IP_TIGHTEN_DENSITY"
  Example: "Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 | Recommendation: Remove '//' to enable switch"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-05:
  description: "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs boolean validation of IP_TIGHTEN_DENSITY switch status.
PASS if switch is enabled (uncommented #DEFINE found).
FAIL if switch is disabled (commented) or missing.

**Sample Output (PASS):**
```
Status: PASS
Reason: IP_TIGHTEN_DENSITY switch found and enabled in DRC rule deck configuration
INFO01:
  - Switch: IP_TIGHTEN_DENSITY | Status: ENABLED | File: do_cmd_3star_DRC_sourceme | Line: 42
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: IP_TIGHTEN_DENSITY switch not found or disabled in DRC rule deck - must be uncommented
ERROR01:
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 | Recommendation: Remove '//' to enable switch
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-05:
  description: "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IP_TIGHTEN_DENSITY switch check is informational for legacy designs"
      - "Note: Disabled switch is acceptable for chip-level DRC where local density is not critical"
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
  - "Explanation: IP_TIGHTEN_DENSITY switch check is informational for legacy designs"
  - "Note: Disabled switch is acceptable for chip-level DRC where local density is not critical"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-05:
  description: "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
  requirements:
    value: 1
    pattern_items:
      - "IP_TIGHTEN_DENSITY"  # Directive name to validate (must be ENABLED)
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- pattern_items contains DIRECTIVE NAMES to search for and validate
- Each directive must be in ENABLED state (uncommented #DEFINE)
- Semantic level: DIRECTIVE NAME (e.g., "IP_TIGHTEN_DENSITY", "CHECK_HIGH_DENSITY")
- NOT full #DEFINE syntax (e.g., NOT "#DEFINE IP_TIGHTEN_DENSITY")
- NOT status values (e.g., NOT "ENABLED" or "DISABLED")

**Check Behavior:**
Type 2 searches for directives listed in pattern_items and validates their status.
PASS if all directives in pattern_items are found and ENABLED (uncommented).
FAIL if any directive is DISABLED (commented) or MISSING.

**Sample Output (PASS):**
```
Status: PASS
Reason: IP_TIGHTEN_DENSITY directive matched and validated as enabled in DRC configuration
INFO01:
  - Switch: IP_TIGHTEN_DENSITY | Status: ENABLED | File: do_cmd_3star_DRC_sourceme | Line: 42
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: IP_TIGHTEN_DENSITY directive not satisfied - switch is commented out or missing from configuration
ERROR01:
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 | Recommendation: Remove '//' to enable switch
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-05:
  description: "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
  requirements:
    value: 1
    pattern_items:
      - "IP_TIGHTEN_DENSITY"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: IP_TIGHTEN_DENSITY requirement is informational for this design phase"
      - "Note: Switch will be enabled in final tapeout DRC deck"
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
  - "Explanation: IP_TIGHTEN_DENSITY requirement is informational for this design phase"
  - "Note: Switch will be enabled in final tapeout DRC deck"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-05:
  description: "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
  requirements:
    value: 1
    pattern_items:
      - "IP_TIGHTEN_DENSITY"  # Directive name to validate
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme"
  waivers:
    value: 2
    waive_items:
      - name: "IP_TIGHTEN_DENSITY"  # Matches pattern_items format
        reason: "Waived - legacy design uses chip-level density rules instead of IP-level"
      - name: "CHECK_HIGH_DENSITY"  # Another directive (for demonstration)
        reason: "Waived - high density check not required for this IP block"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description says "switch" → Use DIRECTIVE NAMES (e.g., "IP_TIGHTEN_DENSITY")
- pattern_items: ["IP_TIGHTEN_DENSITY"] (directive name)
- waive_items.name: "IP_TIGHTEN_DENSITY" (same level as pattern_items)
- DO NOT mix formats: pattern_items="#DEFINE IP_TIGHTEN_DENSITY" with waive_items.name="IP_TIGHTEN_DENSITY"

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same directive validation logic as Type 2, plus waiver classification:
- Match disabled/missing directives against waive_items
- Unwaived disabled directives → ERROR (need fix)
- Waived disabled directives → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all disabled/missing directives are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 [WAIVER]
WARN01 (Unused Waivers):
  - CHECK_HIGH_DENSITY: Waiver not matched - IP_TIGHTEN_DENSITY directive not found in specified state
```

**Sample Output (FAIL - unwaived violation):**
```
Status: FAIL
Reason: IP_TIGHTEN_DENSITY directive not satisfied - switch is commented out or missing from configuration
ERROR01:
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 | Recommendation: Remove '//' to enable switch
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-05:
  description: "Confirm open the IP_TIGHTEN_DENSITY switch in DRC rule deck."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme"
  waivers:
    value: 2
    waive_items:
      - name: "IP_TIGHTEN_DENSITY"  # IDENTICAL to Type 3
        reason: "Waived - legacy design uses chip-level density rules instead of IP-level"
      - name: "CHECK_HIGH_DENSITY"  # IDENTICAL to Type 3
        reason: "Waived - high density check not required for this IP block"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
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
INFO01 (Waived):
  - Switch: IP_TIGHTEN_DENSITY | Status: DISABLED | File: do_cmd_3star_DRC_sourceme | Line: 42 [WAIVER]
WARN01 (Unused Waivers):
  - CHECK_HIGH_DENSITY: Waiver not matched - IP_TIGHTEN_DENSITY directive not found in specified state
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-05 --force

# Run individual tests
python IMP-12-0-0-05.py
```

---

## Notes

**Important Considerations:**

1. **File Flexibility**: User only needs to specify one file - either `do_pvs_DRC_pvl.log` (Pegasus) or `do_cmd_3star_DRC_sourceme` (Calibre). The checker will process whichever file exists.

2. **Switch Semantics**: The IP_TIGHTEN_DENSITY switch controls local density checking at IP/macro/block level. When enabled, it tightens density rules to ensure proper metal distribution in hierarchical designs.

3. **Pattern Matching**: The checker uses regex patterns to handle various formatting styles:
   - Flexible whitespace (spaces/tabs)
   - Inline comments (// or /* */)
   - Multiple occurrences (last one wins)

4. **Edge Cases**:
   - If switch appears multiple times, the last occurrence determines the final state
   - Empty files or files with only comments will result in MISSING status
   - Case-sensitive matching (IP_TIGHTEN_DENSITY must be exact)

5. **Waiver Strategy**:
   - Type 3/4: Use waivers when disabled switch is acceptable for specific design contexts (e.g., chip-level DRC where IP-level density is not critical)
   - Type 1/2 with value=0: Use for informational tracking when switch status is not enforced

6. **Known Limitations**:
   - Does not validate the actual DRC rule implementation, only the switch configuration
   - Does not check if the switch has any effect (i.e., if corresponding rules exist)
   - Assumes standard Calibre/Pegasus #DEFINE syntax