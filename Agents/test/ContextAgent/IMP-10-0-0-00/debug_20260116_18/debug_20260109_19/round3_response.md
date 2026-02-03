<section2>
## 2. Check Logic

Based on description "Confirm the netlist/spef version is correct", the following items require validation:

**Validation Items**:

### 2.1 Netlist File Loading Status
- **Purpose**: Verify netlist file was successfully accessed and parsed
- **Completeness definition**: 
  - `parsed_fields.netlist.loaded == True`
  - File path is accessible and readable
- **Validation type**: Existence check (Boolean)
- **PASS condition**: Netlist file successfully loaded
- **FAIL condition**: File not found, access denied, or parsing error

### 2.2 Netlist Version Completeness
- **Purpose**: Verify netlist contains complete version metadata
- **Completeness definition**:
  - `parsed_fields.netlist.tool_name` exists and is non-empty
  - `parsed_fields.netlist.tool_version` exists and is non-empty
  - `parsed_fields.netlist.timestamp` exists and is non-empty
  - `parsed_fields.netlist.format` exists and is non-empty
- **Validation type**: Existence check (Boolean)
- **PASS condition**: All mandatory version fields present and non-empty
- **FAIL condition**: Any mandatory field missing or empty

### 2.3 SPEF File Loading Status
- **Purpose**: Verify SPEF file was successfully accessed and parsed
- **Completeness definition**:
  - `parsed_fields.spef.loaded == True`
  - File path is accessible and readable
- **Validation type**: Existence check (Boolean)
- **PASS condition**: SPEF file successfully loaded
- **FAIL condition**: File not found, access denied, or parsing error

### 2.4 SPEF Version Completeness
- **Purpose**: Verify SPEF contains complete version metadata
- **Completeness definition**:
  - `parsed_fields.spef.tool_name` exists and is non-empty
  - `parsed_fields.spef.tool_version` exists and is non-empty
  - `parsed_fields.spef.timestamp` exists and is non-empty
  - `parsed_fields.spef.standard_version` exists and is non-empty
- **Validation type**: Existence check (Boolean)
- **PASS condition**: All mandatory version fields present and non-empty
- **FAIL condition**: Any mandatory field missing or empty

**Pattern Matching**:
- Items requiring pattern matching: None (Type 4 checker - Boolean validation only)
- Items with existence check only: All items (2.1, 2.2, 2.3, 2.4)

**Pattern Correspondence Order**: 
- Not applicable (requirements.value = N/A, no pattern_items defined)

**Overall Pass/Fail Logic**:
- **PASS**: All four validation items pass (both netlist and SPEF files loaded successfully with complete version information)
- **FAIL**: Any validation item fails (file loading failure OR incomplete version metadata)
- **Edge Cases**:
  - If netlist loads but SPEF fails → FAIL (unless waived)
  - If version fields exist but contain only whitespace → FAIL (treated as empty)
  - If files are compressed (.gz) → Must decompress before parsing
  - If multiple version headers exist → Use first occurrence

**Validation Sequence**:
1. Check netlist loading status (Item 2.1)
2. If loaded, validate netlist version completeness (Item 2.2)
3. Check SPEF loading status (Item 2.3)
4. If loaded, validate SPEF version completeness (Item 2.4)
5. Return PASS only if all items pass

</section2>