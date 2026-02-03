# IMP-10-0-0-00: Confirm the netlist/spef version is correct.

## Overview

**Check ID:** IMP-10-0-0-00  
**Description:** Confirm the netlist/spef version is correct.  
**Category:** Static Timing Analysis (STA) Configuration Verification  
**Input Files:** 
- `${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log`

This checker verifies that the correct versions of netlist and SPEF files are used in Static Timing Analysis (STA). It performs a two-step validation: First, it checks whether netlist and SPEF files exist in the log. Second, it opens the extracted netlist and SPEF files to capture the current version information from within the files themselves. The checker ensures version traceability and configuration correctness by validating that the design is analyzed with the intended file versions.

---

## Check Logic

### Input Parsing

The checker performs a two-step validation process:

**Step 1: Check for netlist and SPEF existence in STA log**

The checker first parses the Tempus STA log file to verify:
1. **Netlist file path** - from `read_netlist` command
2. **SPEF status** - whether SPEF was read or skipped (with reason)

**Step 2: Extract version information from actual files**

After confirming file existence, the checker:
1. **Opens the extracted netlist file** - reads version information from file header/comments
2. **Opens the extracted SPEF file** - reads version information from SPEF header
3. **Captures current versions** - extracts version tags, timestamps, or revision identifiers

**Key Patterns:**

```python
# Step 1: Log file patterns for existence check
# Pattern 1: Netlist file reading command
pattern_netlist = r'read_netlist\s+([^\s]+\.v(?:\.gz)?)'
# Example: "<CMD> read_netlist C:\Users\yuyin\Desktop\CHECKLIST\IP_project_folder\dbs\phy_cmn_phase_align_digtop.v.gz"

# Pattern 2: SPEF reading status (skipped case)
pattern_spef_skip = r'\[INFO\]\s+Skipping SPEF reading as (.+)'
# Example: "[INFO] Skipping SPEF reading as we are writing post-synthesis SDF files"

# Pattern 3: SPEF file reading (if present)
pattern_spef_read = r'read_spef\s+([^\s]+\.spef(?:\.gz)?)'
# Example: "read_spef /path/to/design.spef.gz"

# Step 2: File content patterns for version extraction
# Pattern 4: Netlist version from file header - extract timestamp
pattern_netlist_version = r'Generated on:\s*(.+?)\s+\w+\s+\((.+?)\)'
# Example: "Generated on: Nov 18 2025 15:58:15 IST (Nov 18 2025 10:28:15 UTC)"
# Captures: Group 1 = "Nov 18 2025 15:58:15 IST", Group 2 = "Nov 18 2025 10:28:15 UTC"

# Pattern 5: SPEF version from file header - extract timestamp
pattern_spef_version = r'Generated on:\s*(.+?)\s+\w+\s+\((.+?)\)|DESIGN\s+"(.+?)"\s+DATE\s+"(.+?)"'
# Example: "Generated on: Nov 18 2025 15:58:15 IST (Nov 18 2025 10:28:15 UTC)"
# Or: 'DESIGN "top_module" DATE "Nov 18 2025"'

# Pattern 6: Parasitics mode detection (for validation)
pattern_parasitics = r'#\s*Parasitics Mode:\s*(.+)'
# Example: "# Parasitics Mode: No SPEF/RCDB"

# Pattern 7: Top-level design name
pattern_top_design = r'Top level cell is\s+(\S+)'
# Example: "Top level cell is phy_cmn_phase_align_digtop."

# Pattern 8: Tool version
pattern_tool_version = r'Program version\s*=\s*([\d\.\-\w]+)'
# Example: "Program version = 23.15-s108_1"
```

### Detection Logic

**Step 1: Verify file existence in log**

1. **Parse netlist information:**
   - Search for `read_netlist` command to extract netlist file path
   - Extract filename from full path for version identification
   - Store design name from netlist filename

2. **Determine SPEF status:**
   - Check for "Skipping SPEF reading" message → Extract skip reason
   - OR check for `read_spef` command → Extract SPEF file path
   - Verify against "Parasitics Mode" summary for consistency

**Step 2: Extract version from actual files**

3. **Open and read netlist file:**
   - Locate netlist file from extracted path
   - Handle compressed files (.gz) if necessary
   - Search file header for "Generated on:" timestamp
   - Extract timestamp in format: "Nov 18 2025 15:58:15 IST (Nov 18 2025 10:28:15 UTC)"
   - Use UTC timestamp as canonical version identifier

4. **Open and read SPEF file (if loaded):**
   - Locate SPEF file from extracted path
   - Handle compressed files (.gz) if necessary
   - Search SPEF header for "Generated on:" timestamp or DATE field
   - Extract timestamp as version identifier
   - Use UTC timestamp as canonical version identifier

5. **Build version summary:**
   - Combine netlist timestamp + SPEF timestamp into single identifier
   - Format: `"Netlist: <filename> (Generated: <UTC_timestamp>) | SPEF: <status> (Generated: <UTC_timestamp>)"`
   - Include design name and tool version for traceability

6. **Validation:**
   - Confirm netlist file exists and timestamp was successfully extracted
   - Verify SPEF status is explicitly stated (loaded or skipped with reason)
   - If SPEF loaded, confirm SPEF timestamp was successfully extracted
   - Check for any version-related warnings or errors in log

---

## Output Behavior (CRITICAL - Determines Type 2/3 Logic!)

**Check Mode:** `status_check`

### Mode 2: `status_check` - 状态检查  
**Use when:** pattern_items are items to CHECK STATUS, only output matched items

```
pattern_items: ["Nov 18 2025 10:28:15 UTC", "SPEF: Skipped"]
Input file contains: Nov 18 2025 10:28:15 UTC (correct), SPEF: Skipped (correct), other_config (not in pattern)

Result:
  found_items:   Nov 18 2025 10:28:15 UTC, SPEF: Skipped    ← Pattern matched AND status correct
  missing_items: (none)                                      ← All patterns have correct status
  (other_config not output - not in pattern_items)

PASS: All matched items have correct status
FAIL: Some matched items have wrong status (or pattern not matched)
```

**Selected Mode for this checker:** `status_check`

**Rationale:** This checker validates that specific netlist/SPEF versions are used in STA by extracting timestamp information directly from the files. The `pattern_items` represent expected timestamp identifiers (netlist generation timestamps, SPEF timestamps/status) that should be found after opening and reading the actual files. The checker reports only items matching the pattern_items and verifies their status is correct. Items not in pattern_items (e.g., other configuration settings) are ignored. This is a status check because we're validating that the extracted timestamps from files match expected values, not just checking for existence of any timestamp information.

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
item_desc = "Confirm the netlist/spef version is correct."

# PASS case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_desc_type1_4 = "Netlist and SPEF files found and timestamp information extracted successfully"
# Type 2/3: Pattern checks - emphasize "matched/satisfied" (pattern validation)
found_desc_type2_3 = "All required netlist/SPEF timestamps matched expected configuration after file extraction"

# PASS reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "found/not found" (existence)
found_reason_type1_4 = "Netlist and SPEF files found in log, timestamp information extracted from actual files"
# Type 2/3: Pattern checks - emphasize pattern matching terms (matched|satisfied|validated|compliant|fulfilled)
found_reason_type2_3 = "All required netlist/SPEF timestamps matched and validated after extracting timestamp from actual files"

# FAIL case descriptions - Split by Type semantics (API-026)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_desc_type1_4 = "Netlist or SPEF files not found or timestamp information extraction failed"
# Type 2/3: Pattern checks - emphasize pattern mismatch
missing_desc_type2_3 = "Expected netlist/SPEF timestamps not satisfied after file extraction or timestamp mismatch detected"

# FAIL reasons - Split by Type semantics (ALL Types need these)
# Type 1/4: Boolean checks - emphasize "not found" (absence)
missing_reason_type1_4 = "Required netlist or SPEF files not found in log or timestamp information not extracted from files"
# Type 2/3: Pattern checks - emphasize pattern mismatch terms (not satisfied|missing|failed)
missing_reason_type2_3 = "Expected netlist/SPEF timestamps not satisfied after file extraction - timestamp mismatch or extraction failed"

# WAIVED case descriptions (ALL Types need these)
# Type 1/2 use in waiver=0 mode for waive_items comments
# Type 3/4 use for actual waived violations
waived_desc = "Netlist/SPEF timestamp mismatch waived"

# WAIVED reasons (Type 3/4 ONLY - actual waiver logic)
waived_base_reason = "Netlist/SPEF timestamp mismatch waived per design team approval"

# UNUSED waivers (Type 3/4 ONLY)
unused_desc = "Unused netlist/SPEF timestamp waiver entries"
unused_waiver_reason = "Waiver not matched - no corresponding timestamp mismatch found after file extraction"
```

### INFO01/ERROR01 Display Format

```
INFO01 (Clean/Pass items):
  Format: "Netlist: <filename> (Generated: <UTC_timestamp>) | SPEF: <status> (Generated: <UTC_timestamp>) | Design: <top_design> | Tool: <tool_version>"
  Example: "Netlist: phy_cmn_phase_align_digtop.v.gz (Generated: Nov 18 2025 10:28:15 UTC) | SPEF: Skipped (post-synthesis) | Design: phy_cmn_phase_align_digtop | Tool: 23.15-s108_1"

ERROR01 (Violation/Fail items):
  Format: "TIMESTAMP MISMATCH: <description> | Expected: <expected_timestamp> | Found: <actual_timestamp>"
  Example: "TIMESTAMP MISMATCH: Netlist timestamp | Expected: Nov 18 2025 10:28:15 UTC | Found: Nov 15 2025 08:15:30 UTC"
```

---

## Type 1: Boolean Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-00:
  description: "Confirm the netlist/spef version is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"
  waivers:
    value: N/A
    waive_items: []
```

**Check Behavior:**
Type 1 performs custom boolean validation in two steps:
1. Confirms that netlist and SPEF file paths are present in the STA log
2. Opens the extracted netlist and SPEF files to extract timestamp information

The checker verifies:
- Netlist file was successfully read (read_netlist command found)
- Netlist file can be opened and timestamp extracted from file header
- SPEF status is explicitly stated (either loaded or skipped with reason)
- If SPEF loaded, SPEF file can be opened and timestamp extracted
- Top-level design name matches netlist filename
- Tool version is recorded for compatibility tracking

PASS if all files are found and timestamp information is successfully extracted.
FAIL if any required files are missing or timestamp extraction fails.

**Sample Output (PASS):**
```
Status: PASS
Reason: Netlist and SPEF files found in log, timestamp information extracted from actual files
INFO01:
  - Netlist: phy_cmn_phase_align_digtop.v.gz (Generated: Nov 18 2025 10:28:15 UTC) | SPEF: Skipped (post-synthesis) | Design: phy_cmn_phase_align_digtop | Tool: 23.15-s108_1
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Required netlist or SPEF files not found in log or timestamp information not extracted from files
ERROR01:
  - TIMESTAMP EXTRACTION FAILED: Netlist file found but timestamp information not present in file header
```

### Type 1 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-10-0-0-00:
  description: "Confirm the netlist/spef version is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Timestamp check is informational only for post-synthesis STA"
      - "Note: SPEF is intentionally skipped during post-synthesis analysis - parasitics not required at this stage"
      - "Note: Timestamp extraction from files may fail for legacy netlists without timestamp headers"
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
  - "Explanation: Timestamp check is informational only for post-synthesis STA"
  - "Note: SPEF is intentionally skipped during post-synthesis analysis - parasitics not required at this stage"
  - "Note: Timestamp extraction from files may fail for legacy netlists without timestamp headers"
INFO02 ([WAIVED_AS_INFO] - violations converted to PASS, shown as INFO):
  - TIMESTAMP EXTRACTION FAILED: Netlist file found but timestamp information not present in file header [WAIVED_AS_INFO]
```

---

## Type 2: Value Check

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-00:
  description: "Confirm the netlist/spef version is correct."
  requirements:
    value: 2
    pattern_items:
      - "Nov 18 2025 10:28:15 UTC"  # Expected netlist timestamp (extracted from file)
      - "SPEF: Skipped"              # Expected SPEF status
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"
  waivers:
    value: N/A
    waive_items: []
```

🛑 CRITICAL RULE for pattern_items:
- Description contains "version" → Use TIMESTAMP IDENTIFIERS extracted from files
- For netlist: Use UTC TIMESTAMP extracted from "Generated on:" field (e.g., "Nov 18 2025 10:28:15 UTC")
- For SPEF: Use STATUS (e.g., "SPEF: Skipped") OR UTC TIMESTAMP if loaded (e.g., "Nov 18 2025 10:28:15 UTC")
- DO NOT use filenames: "design.v.gz"
- DO NOT use full paths: "C:\Users\...\design.v.gz"
- DO NOT use display format: "Netlist: design.v.gz (Generated: Nov 18 2025 10:28:15 UTC)"

**Check Behavior:**
Type 2 performs two-step validation:
1. Searches for netlist and SPEF files in the STA log
2. Opens the files and extracts timestamp information
3. Compares extracted timestamps against expected pattern_items

This is a **requirement check** - verifying that the extracted timestamps from files match expected values.

PASS if missing_items is empty (all required timestamps found and matched after file extraction).
FAIL if any pattern_items are not found or have incorrect timestamp after extraction.

**Sample Output (PASS):**
```
Status: PASS
Reason: All required netlist/SPEF timestamps matched and validated after extracting timestamp from actual files
INFO01:
  - Netlist: phy_cmn_phase_align_digtop.v.gz (Generated: Nov 18 2025 10:28:15 UTC) | SPEF: Skipped (post-synthesis) | Design: phy_cmn_phase_align_digtop | Tool: 23.15-s108_1
```

**Sample Output (FAIL):**
```
Status: FAIL
Reason: Expected netlist/SPEF timestamps not satisfied after file extraction - timestamp mismatch or extraction failed
ERROR01:
  - TIMESTAMP MISMATCH: Netlist timestamp | Expected: Nov 18 2025 10:28:15 UTC | Found: Nov 15 2025 08:15:30 UTC (extracted from file header)
```

### Type 2 Variant: waivers.value=0 (Forced PASS Mode)

**Configuration:**
```yaml
IMP-10-0-0-00:
  description: "Confirm the netlist/spef version is correct."
  requirements:
    value: 2
    pattern_items:
      - "Nov 18 2025 10:28:15 UTC"
      - "SPEF: Skipped"
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"
  waivers:
    value: 0  # CRITICAL: value=0 triggers forced PASS mode (NOT waiver logic!)
    waive_items:  # IMPORTANT: Use PLAIN STRING format (NOT name/reason dict!)
      - "Explanation: Timestamp check is informational for post-synthesis flow"
      - "Note: Different netlist timestamps may be used during iterative debug - timestamp tracking is for reference only"
      - "Note: Timestamp extraction may fail for files without proper timestamp headers"
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
  - "Explanation: Timestamp check is informational for post-synthesis flow"
  - "Note: Different netlist timestamps may be used during iterative debug - timestamp tracking is for reference only"
  - "Note: Timestamp extraction may fail for files without proper timestamp headers"
INFO02 ([WAIVED_AS_INFO] - errors converted to PASS, shown as INFO):
  - TIMESTAMP MISMATCH: Netlist timestamp | Expected: Nov 18 2025 10:28:15 UTC | Found: Nov 15 2025 08:15:30 UTC (extracted from file header) [WAIVED_AS_INFO]
```

---

## Type 3: Value Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-00:
  description: "Confirm the netlist/spef version is correct."
  requirements:
    value: 2
    pattern_items:
      - "Nov 18 2025 10:28:15 UTC"  # Expected netlist timestamp (extracted from file)
      - "SPEF: Skipped"              # Expected SPEF status
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"
  waivers:
    value: 2
    waive_items:
      - name: "Nov 15 2025 08:15:30 UTC"  # Waived netlist timestamp (extracted from file)
        reason: "Waived - legacy netlist timestamp Nov 15 2025 08:15:30 UTC approved for post-synthesis debug flow"
      - name: "SPEF: Loaded"  # Waived SPEF status
        reason: "Waived - SPEF loading acceptable for this analysis mode per design team"
```

🛑 CRITICAL RULE for pattern_items AND waive_items.name:
- BOTH must be at SAME semantic level as description!
- Description contains "version" → Both use TIMESTAMP IDENTIFIERS extracted from files
- For netlist: Use UTC TIMESTAMP (e.g., "Nov 18 2025 10:28:15 UTC")
- For SPEF: Use STATUS (e.g., "SPEF: Skipped") OR UTC TIMESTAMP (e.g., "Nov 18 2025 10:28:15 UTC")
- waive_items.name MUST match the format of pattern_items
- DO NOT mix: pattern_items="Nov 18 2025 10:28:15 UTC" with waive_items.name="design.v.gz"

**Check Behavior:**
Type 3 = Type 2 + waiver support.
Same two-step validation as Type 2 (file existence + timestamp extraction), plus waiver classification:
- Match found timestamp mismatches against waive_items
- Unwaived mismatches → ERROR (need fix)
- Waived mismatches → INFO with [WAIVER] tag (approved)
- Unused waivers → WARN with [WAIVER] tag

PASS if all timestamp mismatches are waived.
FAIL if any unwaived mismatches exist.

**Sample Output (with waived items):**
```
Status: PASS
Reason: All violations waived
INFO01 (Waived):
  - Netlist: phy_cmn_phase_align_digtop.v.gz (Generated: Nov 15 2025 08:15:30 UTC) | SPEF: Skipped | Waived - legacy netlist timestamp Nov 15 2025 08:15:30 UTC approved for post-synthesis debug flow [WAIVER]
WARN01 (Unused Waivers):
  - SPEF: Loaded: Waiver not matched - no corresponding violation found after file extraction
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Expected netlist/SPEF timestamps not satisfied after file extraction - timestamp mismatch or extraction failed
ERROR01:
  - TIMESTAMP MISMATCH: Netlist timestamp | Expected: Nov 18 2025 10:28:15 UTC | Found: Nov 12 2025 14:20:45 UTC (extracted from file header)
INFO01 (Waived):
  - SPEF: Loaded | Waived - SPEF loading acceptable for this analysis mode per design team [WAIVER]
```

---

## Type 4: Boolean Check with Waiver Logic

**Configuration (copy to item_data.yaml for testing):**
```yaml
IMP-10-0-0-00:
  description: "Confirm the netlist/spef version is correct."
  requirements:
    value: N/A
    pattern_items: []
  input_files:
    - "${CHECKLIST_ROOT}/IP_project_folder/logs/sta_post_syn.log"
  waivers:
    value: 2
    waive_items:
      - name: "Nov 15 2025 08:15:30 UTC"  # IDENTICAL to Type 3
        reason: "Waived - legacy netlist timestamp Nov 15 2025 08:15:30 UTC approved for post-synthesis debug flow"  # IDENTICAL to Type 3
      - name: "SPEF: Loaded"  # IDENTICAL to Type 3
        reason: "Waived - SPEF loading acceptable for this analysis mode per design team"  # IDENTICAL to Type 3
```

⚠️ CRITICAL: Type 4 waive_items MUST be IDENTICAL to Type 3 waive_items!
- After generating Type 3 configuration, COPY the EXACT waive_items to Type 4
- Use the SAME name values from Type 3
- Use the SAME reason text from Type 3
- This ensures consistency since Type 3 and Type 4 use identical waiver logic

**Check Behavior:**
Type 4 = Type 1 + waiver support.
Same two-step boolean check as Type 1 (validates file existence + timestamp extraction), plus waiver classification:
- Match timestamp violations against waive_items
- Unwaived violations → ERROR
- Waived violations → INFO with [WAIVER] tag
- Unused waivers → WARN with [WAIVER] tag

PASS if all violations are waived.
FAIL if any unwaived violations exist.

**Sample Output (all violations waived):**
```
Status: PASS
Reason: All items waived
INFO01 (Waived):
  - TIMESTAMP MISMATCH: Netlist timestamp | Found: Nov 15 2025 08:15:30 UTC (extracted from file) | Waived - legacy netlist timestamp Nov 15 2025 08:15:30 UTC approved for post-synthesis debug flow [WAIVER]
```

**Sample Output (with unwaived violations):**
```
Status: FAIL
Reason: Required netlist or SPEF files not found in log or timestamp information not extracted from files
ERROR01:
  - TIMESTAMP EXTRACTION FAILED: SPEF file found but timestamp information not present in file header
INFO01 (Waived):
  - TIMESTAMP MISMATCH: Netlist timestamp | Found: Nov 15 2025 08:15:30 UTC (extracted from file) | Waived - legacy netlist timestamp approved [WAIVER]
```

---

## Testing

### Test Commands

```powershell
# Create test snapshots for all types
python common/regression_testing/create_all_snapshots.py --modules 10.0_STA_DCD_CHECK --checkers IMP-10-0-0-00 --force

# Run individual tests
python IMP-10-0-0-00.py
```

---

## Notes

**Two-Step Version Validation:**
- Step 1: Verify netlist and SPEF file paths are present in STA log
- Step 2: Open actual files and extract timestamp information from file headers
- This ensures version traceability from both log records and actual file content
- Critical for reproducing timing analysis results and debugging version-related issues

**Timestamp Extraction from Files:**
- Netlist timestamp typically found in file header comments (e.g., `Generated on: Nov 18 2025 15:58:15 IST (Nov 18 2025 10:28:15 UTC)`)
- SPEF timestamp found in SPEF header (e.g., `Generated on: Nov 18 2025 10:28:15 UTC` or `DATE "Nov 18 2025"`)
- UTC timestamp is used as the canonical version identifier for consistency
- Compressed files (.gz) must be decompressed before reading
- Legacy files without timestamp headers will cause extraction failure

**Parasitics Mode Validation:**
- "No SPEF/RCDB" is expected for post-synthesis STA (wire-load model based)
- Post-layout STA should show "SPEF" or "RCDB" parasitics mode
- Mismatch between SPEF status and parasitics mode indicates configuration error

**Tool Version Compatibility:**
- Tool version (e.g., Tempus 23.15-s108_1) affects netlist/SPEF parsing behavior
- Timestamp mismatches between netlist generation and STA tool may cause issues
- Always verify tool version compatibility with design flow requirements

**Limitations:**
- Checker relies on standard Tempus log format - custom scripts may produce different output
- Compressed files (.gz) require decompression utilities to be available
- Multiple netlist files (hierarchical designs) may require custom parsing logic
- Timestamp extraction depends on standard header format - custom formats may not be recognized

**Known Issues:**
- Windows path format (backslashes) vs Unix format may affect path extraction
- Design name extraction assumes standard naming convention (filename matches top-level module)
- SPEF skip reason is free-form text - may vary across different flow scripts
- File access permissions may prevent opening netlist/SPEF files for timestamp extraction
- Very large compressed files may cause performance issues during decompression
- Timestamp format variations across different EDA tools may require pattern adjustments