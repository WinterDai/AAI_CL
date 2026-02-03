# IMP-7-0-0-00: Block name (e.g: cdn_hs_phy_data_slice)

## Overview

**Check ID:** IMP-7-0-0-00  
**Description:** Block name (e.g: cdn_hs_phy_data_slice)  
**Category:** Design Information Extraction  
**Input Files:** `${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt`

This checker extracts the block/design name from a simple report file. The report contains a single line with the block name, optionally prefixed with "Block name:" and may include inline comments. This is a fundamental design identification check used to verify the correct design is being processed in the INNOVUS implementation flow.

---

## Check Logic

### Input Parsing
The checker reads the IMP-7-0-0-00.rpt file line by line to extract the block name. The file format is simple: a single line containing the block/design name, with optional "Block name:" prefix and inline comments.

**Key Patterns:**
```python
# Pattern 1: Block name with "Block name:" prefix
pattern1 = r'^Block name:\s*(.+?)\s*(?:#.*)?$'
# Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW  # Limit to 10KB"
# Captures: group(1) = "CDN_104H_cdn_hs_phy_data_slice_EW"

# Pattern 2: Standalone block name (fallback - no prefix)
pattern2 = r'^([A-Za-z0-9_]+)\s*(?:#.*)?$'
# Example: "CDN_104H_cdn_hs_phy_data_slice_EW"
# Captures: group(1) = "CDN_104H_cdn_hs_phy_data_slice_EW"

# Pattern 3: Comment detection (for stripping)
pattern3 = r'#.*$'
# Example: "# Limit to 10KB"
# Used to clean inline comments before extraction

# Pattern 4: Empty/whitespace lines (validation)
pattern4 = r'^\s*$'
# Example: "   "
# Used to skip empty lines during parsing
```

### Detection Logic
1. **File Reading**: Open IMP-7-0-0-00.rpt and read line by line
2. **Line Cleaning**: Strip leading/trailing whitespace and inline comments (starting with #)
3. **Pattern Matching**: 
   - First attempt: Match against "Block name:" prefix pattern
   - Fallback: If no prefix found, match standalone alphanumeric name pattern
4. **Extraction**: Extract block name from first successful match (group 1)
5. **Validation**: 
   - Verify block name is not empty after stripping
   - Check for valid characters (alphanumeric and underscore)
   - Warn if unusual characters detected
6. **Error Handling**: If no valid block name found in entire file, raise ERROR01
7. **Return**: First valid block name found (stop after first match)

**Edge Cases:**
- Empty file → ERROR01: "Block name not found"
- Multiple "Block name:" lines → Use first occurrence only
- Inline comments → Strip before extraction
- Whitespace variations → Handle with `\s*` and `.strip()`
- Case sensitivity → Preserve original case

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

**Rationale:** This checker validates that a block name exists in the report file. The pattern_items (if used in Type 2/3) would represent expected block names that should be found. The checker searches for the presence of a valid block name string in the input file.

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
item_desc = "Block name (e.g: cdn_hs_phy_data_slice)"

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Block name found in report"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "Block name matched expected pattern"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Block name successfully extracted from IMP-7-0-0-00.rpt"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "Block name matched and validated against expected patterns"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Block name not found in report"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Expected block name pattern not satisfied"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Block name not found in IMP-7-0-0-00.rpt or invalid format"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Expected block name pattern not satisfied or missing from report"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Block name check waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Block name validation waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused block name waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding block name found in report"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Block name: {block_name}"
  Example: "Block name: CDN_104H_cdn_hs_phy_data_slice_EW"

ERROR01 (Violation/Fail items):
  Format: "ERROR: {error_description}"
  Example: "ERROR: Block name not found in IMP-7-0-0-00.rpt"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
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
Reason: Block name successfully extracted from IMP-7-0-0-00.rpt
INFO01:
  - Block name: CDN_104H_cdn_hs_phy_data_slice_EW
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Block name not found in IMP-7-0-0-00.rpt or invalid format
ERROR01:
  - ERROR: Block name not found in IMP-7-0-0-00.rpt
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Block name extraction is informational only for design tracking"
      - "Note: Missing block name does not block design flow - can be manually specified"
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
  - "Explanation: Block name extraction is informational only for design tracking"
  - "Note: Missing block name does not block design flow - can be manually specified"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - ERROR: Block name not found in IMP-7-0-0-00.rpt [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 2
    pattern_items:
      - "CDN_104H_cdn_hs_phy_data_slice_EW"
      - "cdn_hs_phy_data_slice"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- If description contains "version": Use VERSION IDENTIFIERS ONLY (e.g., "22.11-s119_1")
  ❌ DO NOT use paths: "innovus/221/22.11-s119_1"
  ❌ DO NOT use filenames: "libtech.lef"
- If description contains "filename"/"name": Use COMPLETE FILENAMES (e.g., "design.v")
- If description contains "status": Use STATUS VALUES (e.g., "Loaded", "Skipped")

**Check Behavior:**
Type 2 searches pattern_items in input files.
PASS/FAIL depends on check purpose:
- Violation Check: PASS if found_items empty (no violations)
- Requirement Check: PASS if missing_items empty (all requirements met)

**Sample Output (PASS):**
```
Status: PASS
Reason: Block name matched and validated against expected patterns
INFO01:
  - Block name: CDN_104H_cdn_hs_phy_data_slice_EW
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 2
    pattern_items:
      - "CDN_104H_cdn_hs_phy_data_slice_EW"
      - "cdn_hs_phy_data_slice"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Block name validation is informational - multiple valid design names exist"
      - "Note: Pattern mismatches are expected for derivative designs and do not require fixes"
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
  - "Explanation: Block name validation is informational - multiple valid design names exist"
  - "Note: Pattern mismatches are expected for derivative designs and do not require fixes"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - Block name: unexpected_design_name [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: 2
    pattern_items:
      - "CDN_104H_cdn_hs_phy_data_slice_EW"
      - "cdn_hs_phy_data_slice"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "CDN_104H_cdn_hs_phy_data_slice_EW"
        reason: "Waived - legacy block name approved for backward compatibility"
      - name: "cdn_hs_phy_data_slice"
        reason: "Waived - simplified name used for derivative design variant"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- If description contains "version": 
  ✅ pattern_items: ["22.11-s119_1", "23.10-s200"] (version identifiers)
  ✅ waive_items.name: "22.11-s119_1" (same level as pattern_items)
  ❌ DO NOT mix: pattern_items="innovus/22.11-s119" (path) with waive_items.name="22.11-s119" (version)
- If description contains "filename":
  ✅ pattern_items: ["design.v", "top.v"] (filenames)
  ✅ waive_items.name: "design.v" (same level as pattern_items)

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
  - Block name: CDN_104H_cdn_hs_phy_data_slice_EW [WAIVER]
WARN01 (Unused Waivers):
  - cdn_hs_phy_data_slice: Waiver not matched - no corresponding block name found in report
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-7-0-0-00:
  description: "Block name (e.g: cdn_hs_phy_data_slice)"
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/reports/7.0/IMP-7-0-0-00.rpt"
  waivers:
    value: 2
    waive_items:
      - name: "CDN_104H_cdn_hs_phy_data_slice_EW"
        reason: "Waived - legacy block name approved for backward compatibility"
      - name: "cdn_hs_phy_data_slice"
        reason: "Waived - simplified name used for derivative design variant"
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
  - Block name: CDN_104H_cdn_hs_phy_data_slice_EW [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 7.0_INNOVUS_DESIGN_IN_CHECK --checkers IMP-7-0-0-00 --force

# Run individual tests
python IMP-7-0-0-00.py
```

---

## Notes

**Limitations:**
- Only extracts the first valid block name found in the file
- Does not validate block name against design database or naming conventions
- Assumes block name contains only alphanumeric characters and underscores
- Inline comments (starting with #) are stripped before extraction

**Known Issues:**
- If multiple "Block name:" lines exist, only the first is used
- Unusual characters in block name may trigger warnings but are still extracted
- Empty files or files with only comments will fail the check

**Best Practices:**
- Ensure IMP-7-0-0-00.rpt contains a single, clear block name line
- Use "Block name:" prefix for clarity (though fallback pattern exists)
- Avoid special characters in block names (stick to alphanumeric and underscore)
- Keep inline comments minimal to avoid parsing ambiguity