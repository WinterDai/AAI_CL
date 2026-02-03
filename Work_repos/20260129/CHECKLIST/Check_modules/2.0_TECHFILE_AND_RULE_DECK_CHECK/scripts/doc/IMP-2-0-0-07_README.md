# IMP-2-0-0-07: Confirm LVS rule deck was not modified? If it was, explain in comments field.

## Overview

**Check ID:** IMP-2-0-0-07**Description:** Confirm LVS rule deck was not modified? If it was, explain in comments field.**Category:** 2.0_TECHFILE_AND_RULE_DECK_CHECK**Input Files:**

- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\LVS_pvl.log`

This checker validates that the LVS rule deck file used during verification has not been modified from the golden baseline. It extracts the rule deck path from the LVS log file, compares it against the golden reference (if provided), and reports any differences. The checker supports both simple existence validation (Type 1/4) and detailed file comparison with diff reporting (Type 2/3).

---

## Check Logic

### Input Parsing

**Step 1: Extract Rule Deck Path from LVS Log**

Parse `LVS_pvl.log` to extract the absolute path to the LVS rule deck file from the `include` statement.

**Key Patterns:**

```python
# Pattern 1: Extract LVS rule deck absolute path
pattern1 = r'^include\s+"([^"]+)"'
# Example: 'include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b"'
# Extraction: Group 1 = Full absolute path to rule deck file
```

**Parsing Strategy:**

- Read `LVS_pvl.log` line-by-line
- Search for lines matching `include "*"` pattern
- Extract the path between double quotes as `local_rule`
- `local_rule` is already an absolute path (no further processing needed)

### Detection Logic

**Type 1/4 (No pattern_items):**

- If `local_rule` is successfully extracted and has a value → **PASS**
- If `local_rule` cannot be extracted or is empty → **FAIL**
- Output: Display `local_rule` path in INFO01

**Type 2/3 (With pattern_items):**

1. Store `pattern_items[0]` into `golden_rule` (golden baseline path)
2. Create temporary file `loc_temp`:
   - Copy `local_rule` file content
   - Remove `//` prefix from lines starting with `//#` (uncomment)
   - Save processed content
3. Create temporary file `gold_temp`:
   - Copy `golden_rule` file content
   - Remove `//` prefix from lines starting with `//#` (uncomment)
   - Save processed content
4. Use `difflib` module to compare `loc_temp` and `gold_temp`
5. Save comparison result to `res_temp` file under `self.rpt_path.parent`
6. Evaluation:
   - If `res_temp` is empty (no differences) → **PASS**
   - If `res_temp` contains differences → **FAIL**
7. Output:
   - **PASS**: Display both `local_rule` and `golden_rule` paths
   - **FAIL**: Display only `res_temp` file path (contains diff details)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates the modification status of the LVS rule deck by comparing it against a golden baseline. The `pattern_items` represent the golden rule deck path to check against (not items that should exist in the log). The checker outputs matched items (unmodified rule deck) or missing items (modified rule deck with differences). This is a status validation check, not an existence check.

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
item_desc = "Confirm LVS rule deck was not modified? If it was, explain in comments field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "LVS rule deck path found in log file"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "LVS rule deck matches golden baseline (no modifications detected)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "LVS rule deck path successfully extracted from LVS_pvl.log"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "LVS rule deck content matched golden baseline - no modifications detected"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "LVS rule deck path not found in log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "LVS rule deck modified - differences detected from golden baseline"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "LVS rule deck include statement not found in LVS_pvl.log"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "LVS rule deck content differs from golden baseline - see diff report for details"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "LVS rule deck modifications waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "LVS rule deck modification waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entries for LVS rule deck"
unused_waiver_reason = "Waiver not matched - no corresponding rule deck modification found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Local rule deck: [absolute_path] | Golden rule deck: [absolute_path]"
  Example: "Local rule deck: C:\IP_project_folder\ruledeck\2.0\DFM_LVS_RC_PEGASUS_N5_1p16M.1.2b | Golden rule deck: C:\IP_project_folder\ruledeck\2.0\origin_lvs"

ERROR01 (Violation/Fail items):
  Format: "Diff report: [res_temp_path]"
  Example: "Diff report: C:\IP_project_folder\reports\2.0\IMP-2-0-0-07_lvs_ruledeck_diff.txt"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-07:
  description: "Confirm LVS rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\LVS_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 validates that the LVS rule deck path can be extracted from the log file.
PASS if `include` statement with rule deck path is found.
FAIL if `include` statement is missing or path is empty.

**Sample Output (PASS):**

```
Status: PASS
Reason: LVS rule deck path successfully extracted from LVS_pvl.log
INFO01:
  - Local rule deck: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: LVS rule deck include statement not found in LVS_pvl.log
ERROR01:
  - LVS rule deck path extraction failed - no include statement found in log file
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-07:
  description: "Confirm LVS rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\LVS_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: LVS rule deck path extraction is informational only for this project"
      - "Note: Missing include statement is acceptable for legacy LVS flows"
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
  - "Explanation: LVS rule deck path extraction is informational only for this project"
  - "Note: Missing include statement is acceptable for legacy LVS flows"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - LVS rule deck path extraction failed - no include statement found in log file [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-07:
  description: "Confirm LVS rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\\Users\\chenweif\\Checker_dev\\CHECKLIST\\CHECKLIST\\IP_project_folder\\ruledeck\\2.0\\origin_lvs"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\LVS_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- pattern_items[0] represents the golden baseline rule deck file path
- This is the absolute path to the reference rule deck for comparison
- The checker will perform file-level diff between local_rule and golden_rule

**Check Behavior:**
Type 2 compares the extracted LVS rule deck against the golden baseline.
PASS if no differences found (files are identical after uncommenting `//#` lines).
FAIL if differences exist (modification detected).

**Sample Output (PASS):**

```
Status: PASS
Reason: LVS rule deck content matched golden baseline - no modifications detected
INFO01:
  - Local rule deck: C:\IP_project_folder\ruledeck\2.0\DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b | Golden rule deck: C:\IP_project_folder\ruledeck\2.0\origin_lvs
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: LVS rule deck content differs from golden baseline - see diff report for details
ERROR01:
  - Diff report: C:\IP_project_folder\reports\2.0\IMP-2-0-0-07_lvs_ruledeck_diff.txt
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
IMP-2-0-0-07:
  description: "Confirm LVS rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\\Users\\chenweif\\Checker_dev\\CHECKLIST\\CHECKLIST\\IP_project_folder\\ruledeck\\2.0\\origin_lvs"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\LVS_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: LVS rule deck modifications are acceptable for this project phase"
      - "Note: Differences from golden baseline are expected during development"
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
  - "Explanation: LVS rule deck modifications are acceptable for this project phase"
  - "Note: Differences from golden baseline are expected during development"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Diff report: C:\IP_project_folder\reports\2.0\IMP-2-0-0-07_lvs_ruledeck_diff.txt [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-07:
  description: "Confirm LVS rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\\Users\\chenweif\\Checker_dev\\CHECKLIST\\CHECKLIST\\IP_project_folder\\ruledeck\\2.0\\origin_lvs"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\LVS_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b"
        reason: "Modification of this rule deck is acceptable for this project"
      - name: "DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2a"
        reason: "Legacy rule deck version approved for backward compatibility testing"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:

- pattern_items[0] is the golden baseline file path
- waive_items.name should be the rule deck filename (extracted from local_rule path)
- Both represent the same semantic level: rule deck identifiers

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same file comparison logic as Type 2, plus waiver classification:

- If differences found, extract rule deck filename from local_rule
- Match filename against waive_items
- Unwaived modifications → ERROR (need explanation)
- Waived modifications → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
  PASS if all modifications are waived.

**Sample Output (with waived items):**

```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b: Modification of this rule deck is acceptable for this project [WAIVER]
WARN01 (Unused Waivers):
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2a: Waiver not matched - no corresponding rule deck modification found
```

**Sample Output (with unwaived violations):**

```
Status: FAIL
Reason: LVS rule deck content differs from golden baseline - see diff report for details
ERROR01:
  - Diff report: C:\IP_project_folder\reports\2.0\IMP-2-0-0-07_lvs_ruledeck_diff.txt
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
IMP-2-0-0-07:
  description: "Confirm LVS rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\LVS_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b"
        reason: "Modification of this rule deck is acceptable for this project"
      - name: "DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2a"
        reason: "Legacy rule deck version approved for backward compatibility testing"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!

- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (validates rule deck path extraction), plus waiver classification:

- If path extraction fails, check against waive_items
- Unwaived failures → ERROR
- Waived failures → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
  PASS if all failures are waived.

**Sample Output:**

```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - DFM_LVS_RC_PEGASUS_N5_1p16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_ALRDL.1.2b: Modification of this rule deck is acceptable for this project [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-07 --force

# Run individual tests
python IMP-2-0-0-07.py
```

---

## Notes

**Implementation Details:**

- The checker uses `difflib.unified_diff()` to generate human-readable diff reports
- Lines starting with `//#` are treated as commented-out sections and are uncommented before comparison
- The `res_temp` diff report file is saved under `self.rpt_path.parent` directory
- Diff report filename format: `IMP-2-0-0-07_lvs_ruledeck_diff.txt`

**Edge Cases:**

- If `local_rule` path does not exist on filesystem → FAIL with file not found error
- If `golden_rule` path does not exist → FAIL with golden baseline not found error
- If both files are empty → PASS (no differences)
- If only `//#` comment differences exist → PASS (comments are normalized)

**Limitations:**

- The checker assumes Windows-style paths (backslashes) in the LVS log file
- Only the first `include` statement matching the pattern is processed
- Binary rule deck files cannot be compared (text-based diff only)
