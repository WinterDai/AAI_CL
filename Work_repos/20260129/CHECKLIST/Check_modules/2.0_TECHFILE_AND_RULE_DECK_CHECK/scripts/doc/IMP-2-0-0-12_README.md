# IMP-2-0-0-12: List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt

## Overview

**Check ID:** IMP-2-0-0-12  
**Description:** List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt  
**Category:** TECHFILE_AND_RULE_DECK_CHECK  
**Input Files:** 
- `${CHECKLIST_ROOT}\IP_project_folder\logs\2.0\COD_pvl.log`

This checker extracts the COD (Cut-On-Diffusion) rule deck filename from the Pegasus PVL verification log file. It parses the `include` statement to identify which COD rule deck was used during physical verification. The checker validates that a COD rule deck was properly loaded and reports the deck name for documentation purposes.

---

## Check Logic

### Input Parsing

The checker scans the COD_pvl.log file to locate the `include` statement that references the COD rule deck file. The rule deck path is extracted from the include directive and the basename (filename only) is returned.

**Key Patterns:**

```python
# Pattern 1: COD rule deck include statement (primary pattern)
pattern1 = r'^include\s+"(.+\.COD)"'
# Example: include "C:\Users\chenweif\Checker_dev\CHECKLIST\CHECKLIST\IP_project_folder\ruledeck\2.0\PLN12FFC_FINcut_AutoGen.09_1a.COD"
# Extracts: Full path to COD file, then extract basename only

# Pattern 2: Alternative include pattern with flexible quotes
pattern2 = r'^include\s+[\'"]?([^\'"]+\.COD)[\'"]?'
# Example: include "ruledeck/2.0/PLN16FFP_FINcut_AutoGen.11b.encrypt.COD"
# Handles both Windows and Unix path formats

# Pattern 3: Parsing rule file header (context validation)
pattern3 = r'^Parsing Rule File\s+(.+\.COD\.pvl)'
# Example: Parsing Rule File scr/cdn_hs_phy_top.COD.pvl ...
# Confirms this is a COD run context
```

**Parsing Strategy:**
1. Scan file line-by-line from top to bottom
2. Search for `include` statements containing `.COD` extension
3. Extract the full path from the include statement
4. Use `os.path.basename()` to extract filename only from the absolute path
5. Return the COD rule deck filename (e.g., `PLN12FFC_FINcut_AutoGen.09_1a.COD`)
6. If no include statement found, return `N/A`

**Edge Cases:**
- No include statement: Return `N/A`
- Multiple includes: Return first COD deck found
- Encrypted decks: Handle `.encrypt` extension (e.g., `PLN16FFP_FINcut_AutoGen.11b.encrypt.COD`)
- Windows paths: Handle backslashes (`C:\Users\...`)
- Unix paths: Handle forward slashes (`/home/...`)
- Empty file: Return `N/A`

### Detection Logic

**Type 1/4 Logic (pattern_items is empty):**
- Extract `cod_rule` from include statement (absolute path)
- Extract basename from `cod_rule` to get filename only
- If `cod_rule` successfully extracted and value exists → **PASS**
- If no include statement found or extraction fails → **FAIL** (but requirements.value="N/A" makes this acceptable)
- Output: The extracted COD rule deck filename

**Type 2/3 Logic (pattern_items contains golden value):**
- Extract `cod_rule` from include statement
- Extract basename from `cod_rule` to get `actual_cod_filename`
- Store `pattern_items[0]` into `golden_cod` (expected COD filename)
- If `actual_cod_filename` == `golden_cod` → **PASS**
- If `actual_cod_filename` != `golden_cod` → **FAIL**
- Output: `actual_cod_filename` (Expected: `golden_cod`)

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `existence_check`

**Selected Mode for this checker:** `existence_check`

**Rationale:** This checker validates the existence and identity of the COD rule deck file. The pattern_items (when provided) represent the expected COD rule deck filename that SHOULD EXIST in the log file's include statement. The checker searches for the include statement, extracts the COD filename, and verifies it matches the expected golden value.

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
item_desc = "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "COD rule deck found in PVL log file"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "COD rule deck matched expected configuration"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "COD rule deck include statement found and extracted successfully"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "COD rule deck filename matched expected golden value"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "COD rule deck not found in PVL log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "COD rule deck does not match expected configuration"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "No COD rule deck include statement found in log file"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "COD rule deck filename does not match expected golden value"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "COD rule deck check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "COD rule deck mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused COD rule deck waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding COD rule deck mismatch found"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: [COD_rule_deck_filename]
  Example: PLN12FFC_FINcut_AutoGen.09_1a.COD

ERROR01 (Violation/Fail items):
  Format: Expected: [golden_cod_filename], Found: [actual_cod_filename]
  Example: Expected: PLN16FFP_FINcut_AutoGen.11b.encrypt.COD, Found: PLN12FFC_FINcut_AutoGen.09_1a.COD
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-12:
  description: "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\COD_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 extracts the COD rule deck filename from the include statement in the PVL log file. If the include statement exists and the filename can be extracted, the check passes and outputs the COD rule deck name. If no include statement is found, it outputs "N/A" (which is acceptable per requirements.value="N/A").

**Sample Output (PASS):**
```
Status: PASS
Reason: COD rule deck include statement found and extracted successfully
INFO01:
  - PLN12FFC_FINcut_AutoGen.09_1a.COD
```

**Sample Output (FAIL - No COD deck found):**
```
Status: PASS
Reason: No COD rule deck found (N/A is acceptable)
INFO01:
  - N/A
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-12:
  description: "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\COD_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: COD check is not applicable for this project."
      - "Note: This design does not require COD dummy fill verification."
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
  - "Explanation: COD check is not applicable for this project."
  - "Note: This design does not require COD dummy fill verification."
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - N/A [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-12:
  description: "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
  requirements:
    value: 1
    pattern_items:
      - "PLN12FFC_FINcut_AutoGen.09_1a.COD"  # Expected COD rule deck filename
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\COD_pvl.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description says "List COD dummy rule deck **name**" → Use COMPLETE FILENAMES
- Extract the COD rule deck filename from the include statement (basename only)
- ✅ Correct: `"PLN12FFC_FINcut_AutoGen.09_1a.COD"` (complete filename)
- ❌ Wrong: `"C:\Users\...\PLN12FFC_FINcut_AutoGen.09_1a.COD"` (full path - too broad)
- ❌ Wrong: `"PLN12FFC"` (partial name - too narrow)

**Check Behavior:**
Type 2 searches for the expected COD rule deck filename in the log file's include statement. The checker extracts the actual COD filename and compares it against the golden value in pattern_items. PASS if the extracted filename matches the expected value, FAIL if mismatch or not found.

**Sample Output (PASS):**
```
Status: PASS
Reason: COD rule deck filename matched expected golden value
INFO01:
  - PLN12FFC_FINcut_AutoGen.09_1a.COD (Expected: PLN12FFC_FINcut_AutoGen.09_1a.COD)
```

**Sample Output (FAIL - Mismatch):**
```
Status: FAIL
Reason: COD rule deck filename does not match expected golden value
ERROR01:
  - Expected: PLN16FFP_FINcut_AutoGen.11b.encrypt.COD, Found: PLN12FFC_FINcut_AutoGen.09_1a.COD
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-2-0-0-12:
  description: "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
  requirements:
    value: 1
    pattern_items:
      - "PLN16FFP_FINcut_AutoGen.11b.encrypt.COD"
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\COD_pvl.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: COD rule deck version mismatch is acceptable for this design phase."
      - "Note: Using legacy COD deck PLN12FFC instead of PLN16FFP per design team approval."
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
  - "Explanation: COD rule deck version mismatch is acceptable for this design phase."
  - "Note: Using legacy COD deck PLN12FFC instead of PLN16FFP per design team approval."
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Expected: PLN16FFP_FINcut_AutoGen.11b.encrypt.COD, Found: PLN12FFC_FINcut_AutoGen.09_1a.COD [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-12:
  description: "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
  requirements:
    value: 1
    pattern_items:
      - "PLN16FFP_FINcut_AutoGen.11b.encrypt.COD"  # Expected COD rule deck filename
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\COD_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "PLN12FFC_FINcut_AutoGen.09_1a.COD"  # Waived legacy COD deck
        reason: "Waived - legacy COD deck approved for this design phase"
      - name: "PLN16FFP_FINcut_AutoGen.10a.COD"  # Waived intermediate version
        reason: "Waived - intermediate COD deck version used for debug runs"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description says "List COD dummy rule deck **name**" → Use COMPLETE FILENAMES
- ✅ pattern_items: `["PLN16FFP_FINcut_AutoGen.11b.encrypt.COD"]` (complete filename)
- ✅ waive_items.name: `"PLN12FFC_FINcut_AutoGen.09_1a.COD"` (same level as pattern_items)
- ❌ DO NOT mix: pattern_items with full path and waive_items.name with filename only

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same pattern search logic as Type 2, plus waiver classification:
- Extract actual COD filename from include statement
- Compare against expected filename in pattern_items
- If mismatch found, check against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag
PASS if all mismatches are waived.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - PLN12FFC_FINcut_AutoGen.09_1a.COD [WAIVER] (Reason: Waived - legacy COD deck approved for this design phase)
WARN01 (Unused Waivers):
  - PLN16FFP_FINcut_AutoGen.10a.COD: Waiver not matched - no corresponding COD rule deck mismatch found
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: COD rule deck filename does not match expected golden value
ERROR01:
  - Expected: PLN16FFP_FINcut_AutoGen.11b.encrypt.COD, Found: PLN16FFP_FINcut_AutoGen.10a.COD
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-2-0-0-12:
  description: "List COD dummy rule deck name (fill N/A if no COD). eg: PLN16FFP_FINcut_AutoGen.11b.encrypt"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}\\IP_project_folder\\logs\\2.0\\COD_pvl.log"
  waivers:
    value: 2
    waive_items:
      - name: "PLN12FFC_FINcut_AutoGen.09_1a.COD"  # SAME as Type 3
        reason: "Waived - legacy COD deck approved for this design phase"  # SAME as Type 3
      - name: "PLN16FFP_FINcut_AutoGen.10a.COD"  # SAME as Type 3
        reason: "Waived - intermediate COD deck version used for debug runs"  # SAME as Type 3
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same boolean check as Type 1 (extract COD filename from include statement), plus waiver classification:
- Extract COD filename from log file
- If specific COD decks should be flagged as violations, match against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag
PASS if all violations are waived.

**Sample Output:**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - PLN12FFC_FINcut_AutoGen.09_1a.COD [WAIVER] (Reason: Waived - legacy COD deck approved for this design phase)
WARN01 (Unused Waivers):
  - PLN16FFP_FINcut_AutoGen.10a.COD: Waiver not matched - no corresponding COD rule deck mismatch found
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 2.0_TECHFILE_AND_RULE_DECK_CHECK --checkers IMP-2-0-0-12 --force

# Run individual tests
python IMP-2-0-0-12.py
```

---

## Notes

**Parsing Strategy:**
- The checker uses `os.path.basename()` to extract only the filename from the absolute path found in the include statement
- This ensures consistent output regardless of whether the log contains Windows or Unix path formats
- The `cod_rule` variable stores the full absolute path, but only the basename is returned as output

**Edge Cases:**
- **Encrypted COD decks**: The checker handles `.encrypt` extension in filenames (e.g., `PLN16FFP_FINcut_AutoGen.11b.encrypt.COD`)
- **Multiple include statements**: If multiple COD includes exist, the checker returns the first one found
- **No COD deck**: If no include statement is found, the checker returns `N/A` (which is acceptable per requirements)
- **Path format variations**: The checker handles both Windows backslashes and Unix forward slashes

**Known Limitations:**
- The checker assumes the include statement format follows standard PVL syntax: `include "path/to/file.COD"`
- If the include statement uses non-standard syntax, the regex pattern may need adjustment
- The checker does not validate whether the COD file actually exists on disk, only that it was referenced in the log