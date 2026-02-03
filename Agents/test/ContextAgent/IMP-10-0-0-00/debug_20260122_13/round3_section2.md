## 2. Check Logic

Based on description "Confirm the netlist/spef version is correct", the following items require validation:

**Validation Items**:

### 2.1 Netlist Loading Status
- **Purpose**: Verify the netlist file was successfully loaded before validating version information
- **Completeness definition**: 
  - `parsed_fields.netlist.loaded` exists AND equals `True` (or "Success")
  - `parsed_fields.netlist.source_file` exists (confirms which file was loaded)
- **Validation type**: Existence check only (no pattern matching required)
- **Pass condition**: Netlist loaded successfully
- **Fail condition**: Netlist loading failed or status is missing

### 2.2 SPEF Loading Status
- **Purpose**: Verify the SPEF file was successfully loaded before validating version information
- **Completeness definition**: 
  - `parsed_fields.spef.loaded` exists AND equals `True` (or "Success")
  - `parsed_fields.spef.source_file` exists (confirms which file was loaded)
- **Validation type**: Existence check only (no pattern matching required)
- **Pass condition**: SPEF loaded successfully
- **Fail condition**: SPEF loading failed or status is missing

### 2.3 Netlist Version Completeness
- **Purpose**: Verify the netlist contains complete and valid version information
- **Completeness definition**: 
  - `parsed_fields.netlist.tool_name` exists and is non-empty
  - `parsed_fields.netlist.version` exists and is non-empty
  - `parsed_fields.netlist.timestamp` exists and is non-empty
  - Combined version string matches expected pattern from `requirements.pattern_items[0]`
- **Validation type**: Pattern matching required
- **Pass condition**: All version fields present AND match expected pattern
- **Fail condition**: Missing version fields OR version pattern mismatch

### 2.4 SPEF Version Completeness
- **Purpose**: Verify the SPEF contains complete and valid version information
- **Completeness definition**: 
  - `parsed_fields.spef.tool_name` exists and is non-empty
  - `parsed_fields.spef.version` exists and is non-empty
  - `parsed_fields.spef.timestamp` exists and is non-empty
  - Combined version string matches expected pattern from `requirements.pattern_items[1]`
- **Validation type**: Pattern matching required
- **Pass condition**: All version fields present AND match expected pattern
- **Fail condition**: Missing version fields OR version pattern mismatch

**Pattern Matching**:
- Items requiring pattern matching: **Item 2.3, Item 2.4**
- Items with existence check only: **Item 2.1, Item 2.2**

**Pattern Correspondence Order**:
- `pattern_items[0]` → **Item 2.3 (Netlist Version Completeness)**
  - Pattern format: `"<tool_name> <version>"` (e.g., `"Genus 21.1|DC 2023.03"`)
  - Multiple alternatives separated by `|` for OR relationship
- `pattern_items[1]` → **Item 2.4 (SPEF Version Completeness)**
  - Pattern format: `"<tool_name> <version>"` (e.g., `"Innovus 21.1|StarRC 2022.06|ICC2 2023.03"`)
  - Multiple alternatives separated by `|` for OR relationship

**Overall Pass/Fail Logic**:
- **PASS**: All four validation items pass
  - Both files loaded successfully (Items 2.1, 2.2)
  - Both files have complete version information matching expected patterns (Items 2.3, 2.4)
- **FAIL**: Any validation item fails
  - File loading failure → Cannot proceed with version validation
  - Incomplete version information → Missing required metadata
  - Version pattern mismatch → Unexpected tool or version detected
- **Edge Cases**:
  - If `requirements.value = 0` (waiver mode), failed items may be waived based on `waivers.waive_items` configuration
  - If netlist loads but SPEF fails, Items 2.1 and 2.3 may still pass (partial success scenario)
  - Empty or malformed version strings are treated as FAIL for completeness items