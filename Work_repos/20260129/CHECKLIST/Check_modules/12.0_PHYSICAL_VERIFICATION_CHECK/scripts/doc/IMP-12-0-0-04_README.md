# IMP-12-0-0-04: Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level.

## Overview

**Check ID:** IMP-12-0-0-04  
**Description:** Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level.  
**Category:** Physical Verification - DRC Configuration Validation  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log` - Pegasus PVL rule deck parsing log
- `${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme` - Calibre DRC configuration file

This checker validates that the DRC rule deck has the `CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` option enabled to properly check for PO.R.19 (input floating gate) violations at the IP level. The check prevents false errors by using primary text labels to identify valid floating gates versus actual violations. This is critical for accurate DRC checking in hierarchical designs where IP-level checks need to distinguish between intentional floating gates (marked by text) and actual design rule violations.

---

## Check Logic

### Input Parsing

**File 1: do_pvs_DRC_pvl.log (Pegasus PVL parsing log)**
This file contains the rule deck parsing output showing which `#DEFINE` directives are enabled.

**Key Patterns:**
```python
# Pattern 1: Detect enabled #DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive
pattern1 = r'^#DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT\s*$'
# Example: "#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"

# Pattern 2: Detect commented/disabled directive
pattern2 = r'^\s*##\s*DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT|^\s*//\s*#DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT'
# Example: "##DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"

# Pattern 3: Extract rule file path being parsed
pattern3 = r'^Parsing Rule File\s+(.+?)\s+\.\.\.'
# Example: "Parsing Rule File scr/tv_chip.DRCwD.pvl ..."

# Pattern 4: Detect all #DEFINE directives for context
pattern4 = r'^#DEFINE\s+(\S+)'
# Example: "#DEFINE FULL_CHIP"
```

**File 2: do_cmd_3star_DRC_sourceme (Calibre DRC configuration)**
This file contains `#DEFINE` switches that control DRC checking behavior.

**Key Patterns:**
```python
# Pattern 5: Active (uncommented) #DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT
pattern5 = r'^\s*#DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT\s*(?://.*)?$'
# Example: "#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT   // Turn on to check PO.R.19 in cell level and avoid false error by following primary text"

# Pattern 6: Commented out #DEFINE (disabled)
pattern6 = r'^\s*//\s*#DEFINE\s+CHECK_FLOATING_GATE_BY_PRIMARY_TEXT\s*(?://.*)?$'
# Example: "//#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT   // Turn on to check PO.R.19 in cell level"

# Pattern 7: Related option CHECK_FLOATING_GATE_BY_TEXT (alternative)
pattern7 = r'^\s*(//)?\s*#DEFINE\s+CHECK_FLOATING_GATE_BY_TEXT\s*(?://.*)?$'
# Example: "//#DEFINE CHECK_FLOATING_GATE_BY_TEXT           // Turn on to avoid PO.R.19 false error from empty IP by following text"

# Pattern 8: IP_PIN_TEXT variable definition
pattern8 = r'^\s*VARIABLE\s+IP_PIN_TEXT\s+"([^"]+)"\s*(?://.*)?$'
# Example: 'VARIABLE IP_PIN_TEXT  "?"    // pin name of IP'
```

### Detection Logic

**Step 1: Parse do_pvs_DRC_pvl.log**
1. Scan file line-by-line to find "Parsing Rule File" section
2. Extract rule deck file path for reporting context
3. Search for active `#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` (pattern1)
4. Check for commented/disabled variants (pattern2)
5. Record line number and status (ENABLED/DISABLED/MISSING)

**Step 2: Parse do_cmd_3star_DRC_sourceme**
1. Scan entire file for active `#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` (pattern5)
2. If not found, check for commented version (pattern6) to distinguish disabled vs missing
3. Extract related `VARIABLE IP_PIN_TEXT` value for context (pattern8)
4. Check for alternative option `CHECK_FLOATING_GATE_BY_TEXT` (pattern7) for potential conflicts

**Step 3: Validation Logic**
1. **SUCCESS**: If either file shows the directive is ENABLED (uncommented `#DEFINE` found)
2. **FAILURE**: If directive is MISSING, COMMENTED OUT, or DISABLED in both files
3. **WARNING**: If alternative option `CHECK_FLOATING_GATE_BY_TEXT` is enabled instead (potential configuration conflict)

**Step 4: Result Aggregation**
- Combine results from both files
- Report file path, line number, and status for each occurrence
- Provide remediation guidance if directive is disabled

**Edge Cases:**
- Directive not present in either file → ERROR: Missing configuration
- Directive commented out in both files → ERROR: Disabled configuration
- Multiple rule files parsed → Track which file contains the directive
- Case sensitivity variations → Handle both `#DEFINE` and `#define`
- Whitespace variations → Regex handles tabs vs spaces
- Both `CHECK_FLOATING_GATE_BY_TEXT` and `CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` enabled → WARNING: Conflicting options

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

**Rationale:** This checker validates that the `CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` directive exists and is enabled in the DRC configuration. The check is looking for the presence of an uncommented `#DEFINE` statement in the rule deck files. This is a classic existence check - the directive should be found in an active (uncommented) state. The checker does not validate status of multiple items, but rather confirms a single configuration option is present and enabled.

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
item_desc = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT DRC option enabled to check PO.R.19 (input floating issue) at IP level"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive found and enabled in DRC rule deck"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive matched and enabled in DRC configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive found enabled in DRC rule deck - PO.R.19 checking is active"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Required DRC option CHECK_FLOATING_GATE_BY_PRIMARY_TEXT matched and validated as enabled"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive not found or disabled in DRC rule deck"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Required DRC option CHECK_FLOATING_GATE_BY_PRIMARY_TEXT not satisfied (missing or disabled)"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive not found or commented out - PO.R.19 input floating check will not run at IP level"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Required DRC option CHECK_FLOATING_GATE_BY_PRIMARY_TEXT not satisfied - directive missing or disabled in configuration"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT configuration check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "DRC option CHECK_FLOATING_GATE_BY_PRIMARY_TEXT configuration waived per design team approval - alternative PO.R.19 checking method in use"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entry for CHECK_FLOATING_GATE_BY_PRIMARY_TEXT configuration"
unused_waiver_reason = "Waiver not matched - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive was found enabled (no violation to waive)"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is ENABLED (line <line_num> in <file_path>)"
  Example: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is ENABLED (line 48 in do_cmd_3star_DRC_sourceme)"

ERROR01 (Violation/Fail items):
  Format: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - <reason> (expected in <file_path>)"
  Example: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - Required for PO.R.19 input floating issue check at IP level (expected in do_pvs_DRC_pvl.log or do_cmd_3star_DRC_sourceme)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-04:
  description: "Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a boolean check to verify that the `CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` directive exists and is enabled (uncommented) in at least one of the DRC configuration files. The checker scans both input files for the active `#DEFINE` statement and returns PASS if found enabled, FAIL if missing or commented out.

**Sample Output (PASS):**
```
Status: PASS
Reason: CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive found enabled in DRC rule deck - PO.R.19 checking is active
INFO01:
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is ENABLED (line 48 in do_cmd_3star_DRC_sourceme)
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive not found or commented out - PO.R.19 input floating check will not run at IP level
ERROR01:
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - Required for PO.R.19 input floating issue check at IP level (expected in do_pvs_DRC_pvl.log or do_cmd_3star_DRC_sourceme)
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-04:
  description: "Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is optional for this design because alternative PO.R.19 checking method is used"
      - "Note: This IP uses CHECK_FLOATING_GATE_BY_TEXT instead for empty IP handling"
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
  - Explanation: CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is optional for this design because alternative PO.R.19 checking method is used
  - Note: This IP uses CHECK_FLOATING_GATE_BY_TEXT instead for empty IP handling
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - Required for PO.R.19 input floating issue check at IP level (expected in do_pvs_DRC_pvl.log or do_cmd_3star_DRC_sourceme) [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-04:
  description: "Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
  requirements:
    value: 1
    pattern_items:
      - "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"  # DRC directive name to verify
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description requires checking DRC option status
- pattern_items contains the DIRECTIVE NAME to search for
- Checker validates that this directive is ENABLED (uncommented) in configuration files
- This is a status check: looking for the directive in an active state

**Check Behavior:**
Type 2 searches for the `CHECK_FLOATING_GATE_BY_PRIMARY_TEXT` directive in input files and validates it is enabled (uncommented). This is a requirement check - PASS if the directive is found in active state (missing_items empty), FAIL if directive is missing or commented out (found_items empty or directive disabled).

**Sample Output (PASS):**
```
Status: PASS
Reason: Required DRC option CHECK_FLOATING_GATE_BY_PRIMARY_TEXT matched and validated as enabled
INFO01:
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is ENABLED (line 48 in do_cmd_3star_DRC_sourceme)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-12-0-0-04:
  description: "Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
  requirements:
    value: 1
    pattern_items:
      - "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: CHECK_FLOATING_GATE_BY_PRIMARY_TEXT check is informational only for this design"
      - "Note: Alternative PO.R.19 checking method approved by design team"
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
  - Explanation: CHECK_FLOATING_GATE_BY_PRIMARY_TEXT check is informational only for this design
  - Note: Alternative PO.R.19 checking method approved by design team
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - Required for PO.R.19 input floating issue check at IP level (expected in do_pvs_DRC_pvl.log or do_cmd_3star_DRC_sourceme) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-04:
  description: "Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
  requirements:
    value: 1
    pattern_items:
      - "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"  # DRC directive name to verify
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"
        reason: "Waived - Design uses alternative PO.R.19 checking method approved by verification team"
      - name: "CHECK_FLOATING_GATE_BY_TEXT"
        reason: "Waived - Alternative directive used for empty IP handling per design specification"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description requires checking DRC directive status
- pattern_items: ["CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"] (directive name)
- waive_items.name: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" (same directive name)
- Both use the DIRECTIVE NAME as the identifier (not file paths, not full error messages)

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2 (search for enabled directive), plus waiver classification:
- If directive is missing/disabled, check against waive_items
- Unwaived missing directive → ERROR (need to enable)
- Waived missing directive → INFO with [WAIVER] tag (approved exception)
- Unused waivers → WARN with [WAIVER] tag
PASS if directive is found enabled OR if missing directive is waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - Waived per design team approval [WAIVER]
WARN01 (Unused Waivers):
  - CHECK_FLOATING_GATE_BY_TEXT: Waiver not matched - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT directive was found enabled (no violation to waive)
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-12-0-0-04:
  description: "Confirm the "#define CHECK_FLOATING_GATE_BY_PRIMARY_TEXT" DRC option in DRC rule deck is open to check PO.R.19 (input floating issue) in IP level."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_pvs_DRC_pvl.log
    - ${CHECKLIST_ROOT}/IP_project_folder/logs/do_cmd_3star_DRC_sourceme
  waivers:
    value: 2
    waive_items:
      - name: "CHECK_FLOATING_GATE_BY_PRIMARY_TEXT"
        reason: "Waived - Design uses alternative PO.R.19 checking method approved by verification team"
      - name: "CHECK_FLOATING_GATE_BY_TEXT"
        reason: "Waived - Alternative directive used for empty IP handling per design specification"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (verify directive is enabled), plus waiver classification:
- If directive is missing/disabled, match against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if directive is enabled OR if violation is waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - CHECK_FLOATING_GATE_BY_PRIMARY_TEXT is NOT ENABLED - Waived per design team approval [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 12.0_PHYSICAL_VERIFICATION_CHECK --checkers IMP-12-0-0-04 --force

# Run individual tests
python IMP-12-0-0-04.py
```

---

## Notes

**Implementation Notes:**
- The checker supports both Pegasus PVL (do_pvs_DRC_pvl.log) and Calibre (do_cmd_3star_DRC_sourceme) DRC configuration formats
- Line-by-line parsing is sufficient as configuration files are typically small (<500 lines)
- Case-sensitive matching is used for `#DEFINE` directives per standard DRC syntax
- Whitespace handling accommodates both tabs and spaces in directive definitions

**Known Limitations:**
- Does not validate the functional correctness of PO.R.19 checking, only configuration presence
- Does not check if IP_PIN_TEXT variable is properly configured (related but separate check)
- Multiple rule file parsing may require tracking which specific file contains the directive

**Related Checks:**
- CHECK_FLOATING_GATE_BY_TEXT (alternative option for empty IP handling)
- IP_PIN_TEXT variable configuration (defines pin name pattern for primary text matching)
- PO.R.19 DRC rule validation (actual design rule check results)

**Remediation Guidance:**
If check fails, enable the directive by:
1. Locate the DRC configuration file (do_cmd_3star_DRC_sourceme or rule deck .pvl file)
2. Find the line: `//#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT`
3. Uncomment by removing `//`: `#DEFINE CHECK_FLOATING_GATE_BY_PRIMARY_TEXT`
4. Verify IP_PIN_TEXT variable is properly configured
5. Re-run DRC to confirm PO.R.19 checking is active