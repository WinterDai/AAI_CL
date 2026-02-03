# IMP-2-0-0-03: Confirm DRC rule deck was not modified? If it was, explain in comments field.

## Overview

**Check ID:** IMP-2-0-0-03
**Description:** Confirm DRC rule deck was not modified? If it was, explain in comments field.
**Category:** DRC Rule Deck Integrity Verification
**Input Files:** ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log

This checker verifies that the DRC rule deck used in the Pegasus DRC run has not been modified from the golden baseline. It extracts the actual rule deck path from the DRC log file and compares its content against the golden rule deck, ignoring commented-out lines (starting with `//#`). The checker uses difflib to perform a detailed comparison and reports any differences found.

---

## Check Logic

### Input Parsing

**Step 1: Extract Local Rule Deck Path**

Parse the DRC log file (`DRC_pvl.log`) to extract the rule deck path from the `include` directive:

**Key Patterns:**

```python
# Pattern 1: Rule deck include directive
pattern1 = r'^include\s+"([^"]+)"'
# Example: 'include "scr/cdn_hs_phy_top.DRCwD.pvl"'
# Extracts: scr/cdn_hs_phy_top.DRCwD.pvl (absolute path to local rule deck)
```

**Parsing Strategy:**

- Read DRC_pvl.log line by line
- Search for lines matching `include "*"` pattern
- Extract the path between double quotes as `local_rule`
- `local_rule` is already an absolute path (or relative to project root)

### Detection Logic

**Type 1/4 (No pattern_items):**

1. Extract `local_rule` path from DRC log file
2. If `local_rule` successfully extracted and file exists → PASS
3. If `local_rule` cannot be extracted or file does not exist → FAIL

**Type 2/3 (With pattern_items - Golden Rule Deck Comparison):**

1. Extract `local_rule` path from DRC log file
2. Get `golden_rule` path from `pattern_items[0]`
3. Create temporary file `loc_temp`:
   - Copy content from `local_rule`
   - Delete string `//` for lines starting with  `//#` (commented-out rules)
   - Save content
4. Create temporary file `gold_temp`:
   - Copy content from `golden_rule`
   - Delete string `//` for lines starting with  `//#` (commented-out rules)
   - Save content
5. Use `difflib.unified_diff()` to compare `loc_temp` and `gold_temp`
6. Save comparison result into file `res_temp`
7. Construct `res_temp` path under  `self.rpt_path.parent` before build output.
8. If `res_temp` is empty (no differences) → PASS
9. If `res_temp` contains differences → FAIL

**Comparison Logic Details:**

- Unify format two temp files by deleting `//` for commented-out rules line.
- Report line-by-line differences with context

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

**Rationale:** This checker validates the modification status of the DRC rule deck by comparing it against a golden baseline (pattern_items[0]). The golden rule deck path is the reference to check against, not an item to search for. The checker reports whether the local rule deck matches (UNMODIFIED status) or differs from (MODIFIED status) the golden baseline. Only the rule deck being validated is output, making this a status check rather than an existence check.

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
item_desc = "DRC rule deck modification status"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "DRC rule deck path found in log file"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "DRC rule deck matches golden baseline (unmodified)"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Rule deck path successfully extracted from DRC log"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Rule deck content matches golden baseline - no modifications detected"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "DRC rule deck path not found in log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "DRC rule deck modified from golden baseline"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Rule deck path not found in DRC log file - cannot verify integrity"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms with diff file reference
missing_reason_type2_3 = "Rule deck content differs from golden baseline - modifications detected"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "DRC rule deck modification waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Rule deck modification waived per project approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused rule deck waiver entry"
unused_waiver_reason = "Waiver entry not matched - no corresponding rule deck modification found"
```

### INFO01/ERROR01 Display Format

The checker uses `build_complete_output()` method's default format:

```
INFO01 (Clean/Pass items):
  Format: "- [item_name]: [found_reason]"
  Example: "- scr/cdn_hs_phy_top.DRCwD.pvl: Rule deck content matches golden baseline - no modifications detected"

ERROR01 (Violation/Fail items):
  Format: "- [item_name]: [missing_reason]"
  Example: "- scr/cdn_hs_phy_top.DRCwD.pvl: Rule deck content differs from golden baseline - modifications detected"
```

Note: The actual output format is controlled by the `found_reason` and `missing_reason` parameters passed to `build_complete_output()`. Customize these reason strings in the "Output Descriptions" section above to match your check requirements.

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-03:
  description: "Confirm DRC rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
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
Reason: Rule deck path successfully extracted from DRC log

Log format (CheckList.rpt):
INFO01:
  - scr/cdn_hs_phy_top.DRCwD.pvl

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: scr/cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck path successfully extracted from DRC log
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Rule deck path not found in DRC log file - cannot verify integrity

Log format (CheckList.rpt):
ERROR01:
  - DRC_pvl.log

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: DRC_pvl.log. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck path not found in DRC log file - cannot verify integrity
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**

```yaml
IMP-2-0-0-03:
  description: "Confirm DRC rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck path extraction is informational only for this project phase"
      - "Note: Missing rule deck path is acceptable during early development"
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
  - "Explanation: Rule deck path extraction is informational only for this project phase"
  - "Note: Missing rule deck path is acceptable during early development"
INFO02:
  - DRC_pvl.log

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Rule deck path extraction is informational only for this project phase. [WAIVED_INFO]
2: Info: DRC_pvl.log. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck path not found in DRC log file - cannot verify integrity [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-03:
  description: "Confirm DRC rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_MAIN.ori"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:

- pattern_items[0] contains the GOLDEN RULE DECK PATH (baseline for comparison)
- This is the absolute path to the original/approved rule deck file
- The checker compares the local rule deck (from DRC log) against this golden baseline
- value: 1 because there is ONE golden rule deck to compare against

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:

- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**

```
Status: PASS
Reason: Rule deck content matches golden baseline - no modifications detected

Log format (CheckList.rpt):
INFO01:
  - scr/cdn_hs_phy_top.DRCwD.pvl

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: scr/cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck content matches golden baseline - no modifications detected
Golden: C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_MAIN.ori
```

**Sample Output (FAIL):**

```
Status: FAIL
Reason: Rule deck content differs from golden baseline - modifications detected

Log format (CheckList.rpt):
ERROR01:
  - scr/cdn_hs_phy_top.DRCwD.pvl

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: scr/cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck content differs from golden baseline - modifications detected

Diff Output (res_temp):
--- golden_rule
+++ local_rule
@@ -125,7 +125,7 @@
 #DEFINE CHECK_LOW_DENSITY
 #DEFINE SHDMIM
-#DEFINE Flip_Chip
+//#DEFINE Flip_Chip
 #DEFINE SHDMIM_KOZ_AP_SPACE_5um_IP
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
IMP-2-0-0-03:
  description: "Confirm DRC rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_MAIN.ori"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Rule deck modifications are acceptable during development phase"
      - "Note: Final verification will be performed before tapeout"
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
  - "Note: Final verification will be performed before tapeout"
INFO02:
  - scr/cdn_hs_phy_top.DRCwD.pvl

Report format (item_id.rpt):
Info Occurrence: 2
1: Info: Explanation: Rule deck modifications are acceptable during development phase. [WAIVED_INFO]
2: Info: scr/cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck content differs from golden baseline - modifications detected [WAIVED_AS_INFO]

Diff Output (res_temp):
--- golden_rule
+++ local_rule
@@ -125,7 +125,7 @@
 #DEFINE CHECK_LOW_DENSITY
 #DEFINE SHDMIM
-#DEFINE Flip_Chip
+//#DEFINE Flip_Chip
 #DEFINE SHDMIM_KOZ_AP_SPACE_5um_IP
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**

```yaml
IMP-2-0-0-03:
  description: "Confirm DRC rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: 1
    pattern_items:
      - "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\origin_MAIN.ori"
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt"
        reason: "Modification of this rule deck is acceptable for this project"
      - name: "cdn_hs_phy_top.DRCwD.pvl"
        reason: "Project-specific rule deck customization approved by design team"
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
  - cdn_hs_phy_top.DRCwD.pvl
WARN01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck modification waived per project approval: Project-specific rule deck customization approved by design team [WAIVER]
Warn Occurrence: 1
1: Warn: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Waiver entry not matched - no corresponding rule deck modification found: Modification of this rule deck is acceptable for this project [WAIVER]
```

**Sample Output (with unwaived violations):**

```
Status: FAIL
Reason: Unwaived rule deck modifications found

Log format (CheckList.rpt):
ERROR01:
  - scr/cdn_hs_phy_top.DRCwD.pvl
WARN01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt

Report format (item_id.rpt):
Fail Occurrence: 1
1: Fail: scr/cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck content differs from golden baseline - modifications detected
Warn Occurrence: 1
1: Warn: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Waiver entry not matched - no corresponding rule deck modification found: Modification of this rule deck is acceptable for this project [WAIVER]
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
IMP-2-0-0-03:
  description: "Confirm DRC rule deck was not modified? If it was, explain in comments field."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log
  waivers:
    value: 2
    waive_items:
      - name: "PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt"
        reason: "Modification of this rule deck is acceptable for this project"
      - name: "cdn_hs_phy_top.DRCwD.pvl"
        reason: "Project-specific rule deck customization approved by design team"
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
  - cdn_hs_phy_top.DRCwD.pvl
WARN01:
  - PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt

Report format (item_id.rpt):
Info Occurrence: 1
1: Info: cdn_hs_phy_top.DRCwD.pvl. In line 15, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Rule deck modification waived per project approval: Project-specific rule deck customization approved by design team [WAIVER]
Warn Occurrence: 1
1: Warn: PLN5LO_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_014.13_1a.encrypt. In line 0, ${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\DRC_pvl.log: Waiver entry not matched - no corresponding rule deck modification found: Modification of this rule deck is acceptable for this project [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-03 --force

# Run individual tests
python IMP-2-0-0-03.py
```

---

## Notes

**Implementation Details:**

- The checker uses `difflib.unified_diff()` for detailed line-by-line comparison
- Comment filtering removes lines starting with `//#` before comparison to ignore documentation changes
- Temporary files (`loc_temp`, `gold_temp`, `res_temp`) are created in system temp directory
- The diff output shows context lines (±3 lines) around each difference for easier debugging

**Limitations:**

- Only compares against a single golden rule deck (pattern_items[0])
- Does not validate rule deck syntax or semantic correctness
- Assumes rule deck paths in DRC log are absolute or relative to project root
- Comment filtering is simple (only `//#` prefix) - does not handle inline comments

**Known Issues:**

- If DRC log contains multiple `include` directives, only the first one is extracted
- Whitespace-only differences are reported as modifications
- No support for comparing multiple rule deck versions simultaneously

**Edge Cases:**

- Empty DRC log file → FAIL (cannot extract rule deck path)
- Missing golden rule deck file → FAIL (cannot perform comparison)
- Identical files with different line endings (CRLF vs LF) → May report false differences
- Rule deck path contains spaces or special characters → Should handle correctly with quoted path extraction
