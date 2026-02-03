# IMP-2-0-0-09: Confirm BUMP rule deck was not modified? If it was, explain in comments field.

## Overview

**Check ID:** IMP-2-0-0-09**Description:** Confirm BUMP rule deck was not modified? If it was, explain in comments field.**Category:** TECHFILE_AND_RULE_DECK_CHECK**Input Files:**

- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\BUMP_pvl.log`

This checker validates that the BUMP DRC rule deck used in physical verification has not been modified from the golden reference version. It extracts the rule deck path from the Pegasus PVL log file, compares it against the golden rule deck by performing a line-by-line diff (ignoring commented lines starting with `//#`), and reports whether the rule deck is unmodified or has been altered. Any modifications must be documented in the comments field.

---

## Check Logic

### Input Parsing

**Step 1: Extract Rule Deck Path from BUMP_pvl.log**

Parse the BUMP DRC log file (`BUMP_pvl.log`) to extract the rule deck include statement. The include path is stored as `local_rule` (absolute path to the rule deck file used in the run).

**Key Patterns:**

```python
# Pattern 1: Rule deck include statement - extracts absolute path to rule deck
pattern1 = r'^include\s+"([^"]+)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a"
# Extraction: Group 1 = Full absolute path to rule deck file
```

**Parsing Strategy:**

- `local_rule` is already an absolute path extracted directly from the include statement
- No additional path resolution needed
- The extracted path points to the actual rule deck file used during DRC execution

### Detection Logic

**Type 1/4 (Boolean Check - No pattern_items):**

- If `local_rule` can be normally extracted and value exists → **PASS**
- If `local_rule` cannot be extracted or no value → **FAIL**
- Output: Display the extracted `local_rule` path

**Type 2/3 (Pattern Check - With pattern_items):**

1. **Extract Paths:**

   - `local_rule`: Extracted from BUMP_pvl.log include statement
   - `golden_rule`: Retrieved from `pattern_items[0]` (golden reference rule deck path)
2. **Prepare Comparison Files:**

   - Copy `local_rule` to temporary file `loc_temp`
   - Copy `golden_rule` to temporary file `gold_temp`
   - For both files: Remove `//` prefix from lines starting with `//#` (uncomment these lines)
   - Save the cleaned versions
3. **Perform Diff Comparison:**

   - Use Python `difflib` module to compare `loc_temp` and `gold_temp`
   - Generate unified diff output
   - Save diff results to `res_temp` file (located under `self.rpt_path.parent`)
4. **Determine PASS/FAIL:**

   - If `res_temp` is empty (no differences) → **PASS**
   - If `res_temp` contains differences → **FAIL**
5. **Output Format:**

   - **PASS**: Output both `local_rule` and `golden_rule` paths
   - **FAIL**: Output only the file path of `res_temp` (diff report for review)

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

**Rationale:** This checker validates the modification status of a specific rule deck (pattern_items[0] = golden reference). The check compares the local rule deck against the golden reference to determine if it has been modified. Only the specified golden rule deck is checked for status (modified vs unmodified), making this a status validation rather than an existence check.

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
item_desc = "Confirm BUMP rule deck was not modified? If it was, explain in comments field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "BUMP rule deck path found in PVL log"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "BUMP rule deck matches golden reference (not modified)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck include path successfully extracted from BUMP_pvl.log"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Rule deck content validated against golden reference - no modifications detected"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "BUMP rule deck path not found in PVL log"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "BUMP rule deck has been modified from golden reference"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Rule deck include statement not found in BUMP_pvl.log or path is empty"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Rule deck content differs from golden reference - modifications detected (see diff report)"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "BUMP rule deck modification waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Rule deck modification approved and waived per project requirements"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entry for BUMP rule deck"
unused_waiver_reason = "Waiver entry not matched - specified rule deck name not found in violations"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Rule deck: [deck_name] | Status: NOT MODIFIED"
  Example: "Rule deck: PN5_CU_BUMP_030.10_1a | Status: NOT MODIFIED"

ERROR01 (Violation/Fail items):
  Format: "Rule deck: [deck_name] | Status: MODIFIED (see diff report: [res_temp_path])"
  Example: "Rule deck: PN5_CU_BUMP_030.10_1a | Status: MODIFIED (see diff report: C:\project\reports\bump_deck_diff.txt)"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-09:
  description: "Confirm BUMP rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BUMP_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs a simple existence check: verify that the rule deck include path can be extracted from the BUMP_pvl.log file. PASS if the path is found and non-empty, FAIL if the include statement is missing or the path is empty.

**Sample Output (PASS):**

```
Status: PASS
Reason: Rule deck include path successfully extracted from BUMP_pvl.log
INFO01:
  - Rule deck: PN5_CU_BUMP_030.10_1a | Path: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Rule deck include statement not found in BUMP_pvl.log or path is empty
ERROR01:
  - BUMP_pvl.log does not contain valid rule deck include statement
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-09:
  description: "Confirm BUMP rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BUMP_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck path extraction is informational only for this project phase"
      - "Note: Missing include statement is acceptable during early development"
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
  - "Explanation: Rule deck path extraction is informational only for this project phase"
  - "Note: Missing include statement is acceptable during early development"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - BUMP_pvl.log does not contain valid rule deck include statement [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-09:
  description: "Confirm BUMP rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\\Users\\chenweif\\Checker_dev\\CHECKLIST\\CHECKLIST\\IP_project_folder\\ruledeck\\2.0\\origin_bump"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BUMP_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 2 compares the local rule deck (extracted from BUMP_pvl.log) against the golden reference rule deck (pattern_items[0]). The checker performs a line-by-line diff after uncommenting lines starting with `//#`. PASS if no differences are found (rule deck not modified), FAIL if differences exist (rule deck has been modified).

**Sample Output (PASS):**

```
Status: PASS
Reason: Rule deck content validated against golden reference - no modifications detected
INFO01:
  - Rule deck: PN5_CU_BUMP_030.10_1a | Status: NOT MODIFIED
  - Local: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PN5_CU_BUMP_030.10_1a
  - Golden: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_bump
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Rule deck content differs from golden reference - modifications detected (see diff report)
ERROR01:
  - Rule deck: PN5_CU_BUMP_030.10_1a | Status: MODIFIED
  - Diff report: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\bump_deck_diff.txt
```

**Implementation For _execute_type2()**

```
def _execute_type2(self) -> CheckResult:
    """Type 2: Rule deck comparison check without waiver support."""
    found_items, missing_items = self._type2_core_logic()
  
    # Step 2: Construct diff file path BEFORE build_complete_output()
    res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
  
    # Step 3: Build missing_reason with diff file path
    missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"
  
    # Step 4: Call build_complete_output with modified reason
    return self.build_complete_output(
        found_items=found_items,
        missing_items=missing_items,
        found_desc=self.FOUND_DESC_TYPE2_3,
        missing_desc=self.MISSING_DESC_TYPE2_3,
        found_reason=self.FOUND_REASON_TYPE2_3,
        missing_reason=missing_reason_with_path  # Use modified reason with path
    )
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-09:
  description: "Confirm BUMP rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\\Users\\chenweif\\Checker_dev\\CHECKLIST\\CHECKLIST\\IP_project_folder\\ruledeck\\2.0\\origin_bump"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BUMP_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck modifications are acceptable for this experimental design"
      - "Note: Differences from golden reference are expected during rule deck tuning phase"
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
  - "Explanation: Rule deck modifications are acceptable for this experimental design"
  - "Note: Differences from golden reference are expected during rule deck tuning phase"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Rule deck: PN5_CU_BUMP_030.10_1a | Status: MODIFIED (see diff report) [WAIVED_AS_INFO]
  - Diff report: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\bump_deck_diff.txt [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-09:
  description: "Confirm BUMP rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\\Users\\chenweif\\Checker_dev\\CHECKLIST\\CHECKLIST\\IP_project_folder\\ruledeck\\2.0\\origin_bump"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BUMP_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "PN5_CU_BUMP_030.10_1a"
        reason: "Modification of this rule deck is acceptable for this project per design team approval"
      - name: "PN5_CU_BUMP_030.10_2b"
        reason: "Custom rule deck variant approved for advanced node testing"
```

**Check Behavior:**
Type 3 = Type 2 + waiver support. Same diff comparison logic as Type 2, plus waiver classification:

- Extract rule deck name from local_rule path
- Match rule deck name against waive_items
- Unwaived modifications → ERROR (need explanation/fix)
- Waived modifications → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if all modifications are waived.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Rule deck: PN5_CU_BUMP_030.10_1a | Status: MODIFIED (waived) [WAIVER]
  - Reason: Modification of this rule deck is acceptable for this project per design team approval
WARN01 (Unused Waivers):
  - PN5_CU_BUMP_030.10_2b: Waiver entry not matched - specified rule deck name not found in violations
```

**Sample Output (with unwaived violations):**

```
Status: FAIL
Reason: Rule deck content differs from golden reference - modifications detected (see diff report)
ERROR01:
  - Rule deck: PN5_CU_BUMP_030.10_1a | Status: MODIFIED
  - Diff report: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\reports\bump_deck_diff.txt
INFO01 (Waived):
  - (none)
WARN01 (Unused Waivers):
  - PN5_CU_BUMP_030.10_1a: Waiver entry not matched - specified rule deck name not found in violations
  - PN5_CU_BUMP_030.10_2b: Waiver entry not matched - specified rule deck name not found in violations
```

**Implementation For _execute_type3()**

```
def _execute_type3(self) -> CheckResult:
    """Type 3: Rule deck comparison check with waiver support."""
    # Step 1: Get found/missing items from core logic
    found_items_base, violations = self._type2_core_logic()
  
    # Step 2: Parse waiver configuration
    waivers = self.get_waivers()
    waive_items_raw = waivers.get('waive_items', [])
    waive_dict = self.parse_waive_items(waive_items_raw)
  
    # Step 3: Split violations into waived and unwaived
    found_items = {}
    waived_items = {}
    missing_items = {}
    used_waivers = set()
  
    for item_name, item_data in found_items_base.items():
        found_items[item_name] = item_data
  
    for viol_name, viol_data in violations.items():
        matched_waiver = self.match_waiver_entry(viol_name, waive_dict)
        if matched_waiver:
            waived_items[viol_name] = viol_data
            used_waivers.add(matched_waiver)
        else:
            missing_items[viol_name] = viol_data
  
    unused_waivers = [w for w in waive_dict.keys() if w not in used_waivers]
  
    # Step 4: Construct diff file path BEFORE build_complete_output()
    res_temp_path = self.rpt_path.parent / f"{self.item_id}_diff.txt"
  
    # Step 5: Build missing_reason with diff file path
    missing_reason_with_path = f"{self.MISSING_REASON_TYPE2_3} - see diff file: {res_temp_path}"
  
    # Step 6: Call build_complete_output with modified reason
    return self.build_complete_output(
        found_items=found_items,
        missing_items=missing_items,
        waived_items=waived_items,
        unused_waivers=unused_waivers,
        waive_dict=waive_dict,
        found_desc=self.FOUND_DESC_TYPE2_3,
        missing_desc=self.MISSING_DESC_TYPE2_3,
        waived_desc=self.WAIVED_DESC,
        found_reason=self.FOUND_REASON_TYPE2_3,
        missing_reason=missing_reason_with_path,  # Use modified reason with path
        waived_base_reason=self.WAIVED_BASE_REASON,
        unused_waiver_reason=self.UNUSED_WAIVER_REASON
    )
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-09:
  description: "Confirm BUMP rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\BUMP_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "PN5_CU_BUMP_030.10_1a"
        reason: "Modification of this rule deck is acceptable for this project per design team approval"
      - name: "PN5_CU_BUMP_030.10_2b"
        reason: "Custom rule deck variant approved for advanced node testing"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!

- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support. Same boolean check as Type 1 (verify rule deck path exists), but if path extraction fails or other violations are detected, match them against waive_items:

- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
  PASS if all violations are waived.

**Sample Output:**

```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - Rule deck path extraction failed for PN5_CU_BUMP_030.10_1a [WAIVER]
  - Reason: Modification of this rule deck is acceptable for this project per design team approval
WARN01 (Unused Waivers):
  - PN5_CU_BUMP_030.10_2b: Waiver entry not matched - specified rule deck name not found in violations
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-09 --force

# Run individual tests
python IMP-2-0-0-09.py
```

---

## Notes

**Limitations:**

- The checker assumes the include statement format is `include "path"` with double quotes
- Only the first include statement matching the pattern is extracted
- The diff comparison ignores lines starting with `//#` (commented debug lines)
- Temporary files (`loc_temp`, `gold_temp`, `res_temp`) are created during comparison and should be cleaned up after execution

**Known Issues:**

- If the rule deck path contains special characters or spaces, ensure proper escaping in the YAML configuration
- The diff report (`res_temp`) path is constructed under `self.rpt_path.parent` - ensure this directory exists and is writable
- Large rule deck files may result in large diff reports if many modifications exist

**Edge Cases:**

- Empty BUMP_pvl.log file → FAIL (no include statement found)
- Multiple include statements → Only the first match is used
- Relative paths in include statement → Should be converted to absolute paths before comparison
- Golden rule deck file missing → FAIL (cannot perform comparison)
- Identical files with different line endings (CRLF vs LF) → May show false differences (consider normalizing line endings)
