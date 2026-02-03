# IMP-2-0-0-10: List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a

## Overview

**Check ID:** IMP-2-0-0-10**Description:** List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a**Category:** TECHFILE_AND_RULE_DECK_CHECK**Input Files:**

- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\FEOL_pvl.log`

This checker extracts and reports the FEOL (Front End Of Line) dummy rule deck name from Pegasus PVL log files. The rule deck name is extracted from the `include` statement in the log file and represents the specific FEOL rule deck version used during physical verification. This is an informational checker that helps track which FEOL rule deck configuration was applied to the design.

---

## Check Logic

### Input Parsing

The checker parses the Pegasus PVL log file to extract the FEOL dummy rule deck name from the `include` statement.

**Key Patterns:**

```python
# Pattern 1: Extract FEOL rule deck filename from include statement (Windows path)
pattern1 = r'include\s+"[^"]*\\([^\\]+\.FEOL)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
# Extracts: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL

# Pattern 2: Extract FEOL rule deck filename from include statement (Unix path)
pattern2 = r'include\s+"[^"]*/([^/]+\.FEOL)"'
# Example: include "/path/to/ruledeck/Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL"
# Extracts: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL

# Pattern 3: Alternative pattern using case-insensitive matching for "Dummy_FEOL"
pattern3 = r'include\s+".*?([Dd]ummy_FEOL_[^"\\]+\.FEOL)"'
# Example: include "C:\path\to\Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
# Extracts: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL
```

**Parsing Strategy:**

1. Scan the FEOL_pvl.log file line-by-line from the beginning
2. Look for lines containing the `include` keyword followed by a quoted path
3. Extract the filename portion that contains "Dummy_FEOL" and ends with ".FEOL" extension
4. Handle both Windows (backslash) and Unix (forward slash) path separators
5. Store the extracted filename as `feol_rule` (absolute path is parsed, but only filename is stored)
6. Stop after finding the first match (only one FEOL rule deck per file expected)

**Edge Cases:**

- Missing include statement: Return empty/None
- Multiple include statements: Take first FEOL match
- Commented out include lines: Skip lines starting with # or //
- Relative vs absolute paths: Extract filename only, ignore path prefix
- Case sensitivity: Use case-insensitive matching for "FEOL" vs "feol"

### Detection Logic

**Type 1/4 Logic (No pattern_items):**

- Step 1: Parse the log file and extract the FEOL rule deck name using the patterns above
- Step 2: Store the extracted filename into `feol_rule` variable
- Step 3: Check if `feol_rule` was successfully extracted and has a valid value
- Step 4: If `feol_rule` exists and is not empty → **PASS**
- Step 5: If `feol_rule` is empty or extraction failed → **FAIL**

**Type 2/3 Logic (With pattern_items):**

- Step 1: Parse the log file and extract the FEOL rule deck name into `feol_rule`
- Step 2: If pattern_items is not empty, retrieve the first item: `golden_feol = pattern_items[0]`
- Step 3: Compare `feol_rule` with `golden_feol`:
  - If `feol_rule == golden_feol` → **PASS**
  - If `feol_rule != golden_feol` → **FAIL**

**Validation:**

- Verify extracted name matches pattern: `Dummy_FEOL_Pegasus_*`
- Ensure `.FEOL` extension is present
- Check for minimum expected components in filename (technology node, version, variant)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

**Use when:** This checker verifies that the FEOL rule deck name exists in the log file and optionally validates it against expected golden values.

### Mode 1: `existence_check` - 存在性检查

**Use when:** pattern_items are items that SHOULD EXIST in input files

```
pattern_items: ["Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"]
Input file contains: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL

Result:
  found_items:   Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL    ← Pattern found in file
  missing_items: (empty)                                   ← All patterns found

PASS: All pattern_items found in file
FAIL: Some pattern_items not found in file
```

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker extracts the FEOL rule deck name from the include statement and validates its existence. For Type 1/4, it simply checks if the rule deck name was successfully extracted. For Type 2/3, it validates that the extracted name matches the expected golden value from pattern_items.

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
item_desc = "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "FEOL dummy rule deck name found in PVL log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "FEOL dummy rule deck name matched expected value"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "FEOL dummy rule deck name successfully extracted from include statement"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "FEOL dummy rule deck name matched and validated against expected golden value"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "FEOL dummy rule deck name not found in PVL log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "FEOL dummy rule deck name does not match expected value"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "FEOL dummy rule deck include statement not found or could not be parsed from log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "FEOL dummy rule deck name does not match expected golden value or pattern not satisfied"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "FEOL dummy rule deck name mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "FEOL dummy rule deck name mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused FEOL rule deck waiver entries"
unused_waiver_reason = "Waiver entry not matched - no corresponding FEOL rule deck mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: [FEOL_rule_deck_filename]
  Example: "Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
  Example: "Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL"

ERROR01 (Violation/Fail items):
  Format: "Expected: [golden_feol], Found: [actual_feol]" (Type 2/3 only)
  Example: "Expected: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL, Found: Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL"
  
  Format: "FEOL rule deck include statement not found in log file" (Type 1/4 when extraction fails)
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-10:
  description: "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\FEOL_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a boolean check to verify that the FEOL dummy rule deck name can be successfully extracted from the PVL log file. PASS if the include statement is found and the rule deck name is extracted; FAIL if the include statement is missing or cannot be parsed.

**Sample Output (PASS):**

```
Status: PASS
Reason: FEOL dummy rule deck name successfully extracted from include statement
INFO01:
  - Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: FEOL dummy rule deck include statement not found or could not be parsed from log file
ERROR01:
  - FEOL rule deck include statement not found in log file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-10:
  description: "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\FEOL_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - it extracts and reports the FEOL rule deck name for documentation purposes"
      - "Note: Missing FEOL rule deck name is acceptable for designs that do not require FEOL dummy fill"
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
  - "Explanation: This check is informational only - it extracts and reports the FEOL rule deck name for documentation purposes"
  - "Note: Missing FEOL rule deck name is acceptable for designs that do not require FEOL dummy fill"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - FEOL rule deck include statement not found in log file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-10:
  description: "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: 1
    pattern_items:
      - "Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\FEOL_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- Description says "List FEOL dummy rule deck name" → Use COMPLETE FILENAMES with .FEOL extension
- ✅ CORRECT: "Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL" (complete filename)
- ❌ WRONG: "5nm_014.13_1a" (version only - too narrow)
- ❌ WRONG: "C:\path\to\Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL" (full path - too broad)

**Check Behavior:**
Type 2 searches for the FEOL rule deck name in the input file and validates it against the expected golden value in pattern_items. PASS if the extracted rule deck name matches the golden value; FAIL if it doesn't match or cannot be extracted.

**Sample Output (PASS):**

```
Status: PASS
Reason: FEOL dummy rule deck name matched and validated against expected golden value
INFO01:
  - Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL (Expected: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL)
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: FEOL dummy rule deck name does not match expected golden value or pattern not satisfied
ERROR01:
  - Expected: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL, Found: Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-10:
  description: "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: 1
    pattern_items:
      - "Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\FEOL_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: This check is informational only - FEOL rule deck version mismatches are acceptable for legacy designs"
      - "Note: Different FEOL rule deck versions may be used across design variants without requiring updates"
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
  - "Explanation: This check is informational only - FEOL rule deck version mismatches are acceptable for legacy designs"
  - "Note: Different FEOL rule deck versions may be used across design variants without requiring updates"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Expected: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL, Found: Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-10:
  description: "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: 1
    pattern_items:
      - "Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\FEOL_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL"
        reason: "Waived - legacy FEOL rule deck version approved for this design variant"
      - name: "Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL"
        reason: "Waived - alternative FEOL rule deck approved for 3nm technology node"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:

- BOTH must be at SAME semantic level as description!
- Description says "List FEOL dummy rule deck name" → Use COMPLETE FILENAMES
- ✅ pattern_items: ["Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL"] (complete filename)
- ✅ waive_items.name: "Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL" (same level as pattern_items)
- ❌ DO NOT mix: pattern_items="Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL" with waive_items.name="014.13_1a" (version only)

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
  - Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL [WAIVER]
WARN01 (Unused Waivers):
  - Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL: Waiver entry not matched - no corresponding FEOL rule deck mismatch found
```

**Sample Output (with unwaived violations):**

```
Status: FAIL
Reason: FEOL dummy rule deck name does not match expected golden value or pattern not satisfied
ERROR01:
  - Expected: Dummy_FEOL_Pegasus_5nm_014.13_1a.FEOL, Found: Dummy_FEOL_Pegasus_5nm_014.10_1a.FEOL
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-10:
  description: "List FEOL dummy rule deck name. eg: Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\FEOL_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL"
        reason: "Waived - legacy FEOL rule deck version approved for this design variant"
      - name: "Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL"
        reason: "Waived - alternative FEOL rule deck approved for 3nm technology node"
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
  - Dummy_FEOL_Pegasus_5nm_014.12_1a.FEOL [WAIVER]
WARN01 (Unused Waivers):
  - Dummy_FEOL_Pegasus_3nm_E_17M_1Xa1Xb1Xc1Xd1Ya1Yb4Y2Yy2Yx2R_014.11_1a.FEOL: Waiver entry not matched - no corresponding FEOL rule deck mismatch found
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-10 --force

# Run individual tests
python IMP-2-0-0-10.py
```

---

## Notes

**Limitations:**

- Only extracts the first FEOL rule deck include statement found in the log file
- Assumes standard Pegasus PVL log format with `include "path"` syntax
- Does not validate the actual contents of the FEOL rule deck file, only the filename

**Known Issues:**

- If multiple FEOL rule decks are included (unusual case), only the first one is reported
- Commented-out include statements are skipped, which is correct behavior but may cause confusion if the active include is later in the file

**Best Practices:**

- For Type 2/3 configurations, ensure pattern_items contains the exact expected FEOL rule deck filename including version and variant identifiers
- Use Type 1 for simple extraction and reporting without validation
- Use Type 2/3 when you need to enforce a specific FEOL rule deck version
- Waiver items should use the complete filename format to match the extraction logic
