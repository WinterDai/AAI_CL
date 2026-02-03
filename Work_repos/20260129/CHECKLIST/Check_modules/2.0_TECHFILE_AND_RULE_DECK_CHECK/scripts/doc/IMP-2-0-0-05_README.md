# IMP-2-0-0-05: Confirm ANT rule deck was not modified? If it was, explain in comments field.

## Overview

**Check ID:** IMP-2-0-0-05
**Description:** Confirm ANT rule deck was not modified? If it was, explain in comments field.
**Category:** Rule Deck Integrity Verification
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log

This checker verifies that the ANT (Antenna) rule deck used in physical verification has not been modified from the original encrypted version. It parses the Pegasus PVL log file to extract the rule deck path, then compares it against a golden reference to detect any modifications. The check ensures design integrity by confirming that only approved, unmodified rule decks are used in the verification flow.

---

## Check Logic

### Input Parsing

**Step 1: Extract Rule Deck Path from ANT Log**
Parse the ANT_pvl.log file to extract the absolute rule deck path from `include` statements. The path between double quotes is stored as `local_rule`.

**Key Patterns:**

```python
# Pattern 1: Rule deck include statement - extracts absolute path to ANT rule deck
pattern1 = r'include\s+"([^"]+)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"
# Extracts: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt
```

### Detection Logic

**Type 1/4 (No pattern_items):**

- If `local_rule` can be extracted and has a value → PASS
- If `local_rule` cannot be extracted or is empty → FAIL
- Output: Display `local_rule` path on PASS

**Type 2/3 (With pattern_items):**

**Step 1: Extract Rule Deck Paths**

- Parse `local_rule` from ANT_pvl.log (absolute path already available)
- Store `pattern_items[0]` as `golden_rule` (baseline reference path)

**Step 2: Prepare Comparison Files**

- Copy `local_rule` to temporary file `loc_temp`
- Copy `golden_rule` to temporary file `gold_temp`
- For both files: Remove `//` prefix from lines starting with `//#` (uncomment debug lines)

**Step 3: Compare Using difflib**

- Use Python's `difflib` module to compare `loc_temp` and `gold_temp`
- Save comparison result to `res_temp` file under `self.rpt_path.parent` directory
- If `res_temp` is empty (no differences) → PASS
- If `res_temp` contains differences → FAIL

**Step 4: Output Results**

- PASS: Output both `local_rule` and `golden_rule` paths
- FAIL: Output only the `res_temp` file path (contains diff details)

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

**Rationale:** This checker validates the modification status of the ANT rule deck by comparing it against a golden reference. The `pattern_items[0]` represents the golden rule deck path to check against. The checker only outputs the status of the specified golden rule deck (whether it matches the local rule deck or not), not all rule decks found in the log. This is a status validation check, not an existence check.

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
item_desc = "Confirm ANT rule deck was not modified? If it was, explain in comments field."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "ANT rule deck path found in log file"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "ANT rule deck matches golden reference (unmodified)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck path successfully extracted from ANT_pvl.log"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Rule deck content matches golden reference - no modifications detected"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "ANT rule deck path not found in log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "ANT rule deck modified - differences detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "No include statement found in ANT_pvl.log or rule deck path is empty"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Rule deck content differs from golden reference - see diff file for details"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "ANT rule deck modification waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Rule deck modification approved and waived per project requirements"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused waiver entry for ANT rule deck"
unused_waiver_reason = "Waiver entry not matched - specified rule deck not found or not modified"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt: Rule deck content matches golden reference - no modifications detected"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- res_temp_diff_20240115.txt: Rule deck content differs from golden reference - see diff file for details"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-05:
  description: "Confirm ANT rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log
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
Reason: Rule deck path successfully extracted from ANT_pvl.log

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt: Rule deck path successfully extracted from ANT_pvl.log
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: No include statement found in ANT_pvl.log or rule deck path is empty

Log format (CheckList.rpt):
ERROR01:
  - ANT_pvl.log

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: ANT_pvl.log. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log: No include statement found in ANT_pvl.log or rule deck path is empty
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-05:
  description: "Confirm ANT rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: ANT rule deck modification check is informational only for this project phase"
      - "Note: Rule deck differences are expected during development and do not require immediate action"
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
  - "Explanation: ANT rule deck modification check is informational only for this project phase"
  - "Note: Rule deck differences are expected during development and do not require immediate action"
INFO02:
  - ANT_pvl.log

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: ANT rule deck modification check is informational only for this project phase. [WAIVED_INFO]
2: Info: ANT_pvl.log. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log: No include statement found in ANT_pvl.log or rule deck path is empty [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-05:
  description: "Confirm ANT rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_ant"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- Description: "Confirm ANT rule deck was not modified"
- Semantic Level: File path comparison (golden reference path)
- pattern_items[0]: Golden rule deck path for comparison
- This is a file-level comparison, not version/status extraction

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:

- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**

```
Status: PASS
Reason: Rule deck content matches golden reference - no modifications detected

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt: Rule deck content matches golden reference - no modifications detected
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Rule deck content differs from golden reference - see diff file for details

Log format (CheckList.rpt):
ERROR01:
  - res_temp_diff_20240115_143022.txt

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: res_temp_diff_20240115_143022.txt. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\res_temp_diff_20240115_143022.txt: Rule deck content differs from golden reference - see diff file for details
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
IMP-2-0-0-05:
  description: "Confirm ANT rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_ant"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck modifications are acceptable during development phase"
      - "Note: Differences from golden reference are expected and tracked separately"
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
  - "Explanation: Rule deck modifications are acceptable during development phase"
  - "Note: Differences from golden reference are expected and tracked separately"
INFO02:
  - res_temp_diff_20240115_143022.txt

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Rule deck modifications are acceptable during development phase. [WAIVED_INFO]
2: Info: res_temp_diff_20240115_143022.txt. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\res_temp_diff_20240115_143022.txt: Rule deck content differs from golden reference - see diff file for details [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-05:
  description: "Confirm ANT rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_ant"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"
        reason: "Approved modification for project-specific antenna rules per design review DR-2024-001"
      - name: "PLN5LO_16M_054_PATCH_ANT.13_1a.encrypt"
        reason: "Waived - patch file with approved customizations for metal stack optimization"
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

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt
WARN01:
  - PLN5LO_16M_054_PATCH_ANT.13_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt: Rule deck modification approved and waived per project requirements: Approved modification for project-specific antenna rules per design review DR-2024-001 [WAIVER]
Warn Occurrence: 1
1: Warn: PLN5LO_16M_054_PATCH_ANT.13_1a.encrypt. In line 0, N/A: Waiver entry not matched - specified rule deck not found or not modified: Waived - patch file with approved customizations for metal stack optimization [WAIVER]
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
IMP-2-0-0-05:
  description: "Confirm ANT rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\ANT_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt"
        reason: "Approved modification for project-specific antenna rules per design review DR-2024-001"
      - name: "PLN5LO_16M_054_PATCH_ANT.13_1a.encrypt"
        reason: "Waived - patch file with approved customizations for metal stack optimization"
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!

- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3 (keep exemption object names consistent)
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

Log format (CheckList.rpt):
INFO01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt
WARN01:
  - PLN5LO_16M_054_PATCH_ANT.13_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt. In line 1, C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014_ANT.13_1a.encrypt: Rule deck modification approved and waived per project requirements: Approved modification for project-specific antenna rules per design review DR-2024-001 [WAIVER]
Warn Occurrence: 1
1: Warn: PLN5LO_16M_054_PATCH_ANT.13_1a.encrypt. In line 0, N/A: Waiver entry not matched - specified rule deck not found or not modified: Waived - patch file with approved customizations for metal stack optimization [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-05 --force

# Run individual tests
python IMP-2-0-0-05.py
```

---

## Notes

**Implementation Details:**

- The checker uses `difflib` module for file comparison, which provides detailed line-by-line differences
- Temporary files (`loc_temp`, `gold_temp`, `res_temp`) are created under `self.rpt_path.parent` directory
- Lines starting with `//#` are treated as commented debug lines and are uncommented before comparison
- The `.encrypt` extension in the rule deck filename indicates an encrypted, unmodified version from the foundry

**Limitations:**

- The checker assumes the ANT_pvl.log contains at least one `include` statement with a valid rule deck path
- Only the first `include` statement is processed (if multiple rule decks are included, only the first is checked)
- The golden reference path must be accessible and readable for comparison
- Binary encrypted files cannot be compared; only text-based rule decks are supported for diff analysis

**Known Issues:**

- Windows path separators (backslashes) in the configuration must be properly escaped in YAML
- Large rule deck files may cause performance issues during diff generation
- The diff output file path is timestamped to avoid conflicts but may accumulate over time
