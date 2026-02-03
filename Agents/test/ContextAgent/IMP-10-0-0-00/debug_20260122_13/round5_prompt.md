<!-- ========================================
     USER PROMPT: Section 4 Guidance & Quality Criteria
     (From user_prompt.md)
========================================= -->

### For Section 4 (Implementation Guide)

1. **Infer data sources** from description and validation needs:
   - "version" → likely in file headers or tool logs
   - "netlist/spef" → STA logs or the files themselves
2. **Suggest search strategies**:
   - Common keywords to look for
   - Typical file locations
   - Parsing patterns
3. **Document special cases**:
   - File not found scenarios
   - Format variations
   - Edge cases

---

## Quality Criteria

Your ItemSpec should:

1. **Be semantically consistent**: All sections should align with the description
2. **Be practically implementable**: Downstream LLM can generate working code
3. **Cover common scenarios**: Address typical cases, not just happy path
4. **Follow framework rules**: Adhere to global_rules.md requirements
5. **Use precise terminology**: Apply correct EDA industry terms

---

## Complete Example Reference

For a fully completed ItemSpec example, refer to:
- **File**: `IMP-10-0-0-00_ItemSpec.md`
- **Description**: "Confirm the netlist/spef version is correct"
- **Shows**: Complete implementation of all 4 sections
- **Use it to**: Understand the expected level of detail and structure

---

## Common Patterns

### For Version Validation Items
- Typical fields: tool_name, version_number, timestamp
- Pattern matching: Use for version numbers and timestamps
- Waivers: Historical versions, format variations

### For File Validation Items
- Typical fields: file_path, loaded_status
- Pattern matching: Usually not needed (existence check only)
- Waivers: Optional files, stage-specific requirements

### For Format Validation Items
- Typical fields: format_version, standard_compliance
- Pattern matching: Use for format specifications
- Waivers: Legacy formats, tool-specific extensions

---

## Example Reasoning Path

Given description: "Confirm the netlist/spef version is correct"

**Step 1 - Understand Requirements**:
- What: Netlist and SPEF files
- Verify: Version information
- Ensure: Correctness (completeness + validity)

**Step 2 - Identify Information Needs**:
- Need to know netlist version → requires tool name, version, date
- Need to know SPEF version → requires generator info, date
- Need to confirm files are accessible → requires loading status

**Step 3 - Design Validation**:
- Item 1: Netlist file loaded successfully
- Item 2: Netlist version complete (name + version + date)
- Item 3: SPEF file loaded successfully
- Item 4: SPEF version complete (info + date)
- Pattern matching: Items 2 and 4 (version content)
- Existence only: Items 1 and 3 (file status)

**Step 4 - Consider Waivers**:
- SPEF may not exist in synthesis stage → waive SPEF items
- May use golden files → waive timestamp mismatches
- Keywords: "synthesis", "SPEF", "golden", "historical"

**Step 5 - Guide Implementation**:
- Data source: STA log file (contains file loading info)
- Keywords: "Reading netlist", "Loading SPEF", version headers
- Strategy: Parse log for loading messages, then extract version from file headers

---


<!-- ========================================
     TASK: Round 5 - Generate Section 4
========================================= -->

<task>
Generate Section 4 (Implementation Guide) of the ItemSpec, ensuring overall quality.
</task>

<!-- ========================================
     CONTEXT: Previous Sections Summary
========================================= -->

<previous_sections_summary>
Section 1 Summary: ## 1. Parsing Logic

**Information to Extract**:

### 1.1 Netlist File Information
- **Purpose**: Extract netlist loading status and version metadata to verify the netlist file was successfully read and contains complete version information
- **Key Fields**:
  - `loaded`: Boolean or status string indicating whether the netlist was successfully loaded (e.g., "Success", "Failed", True/False)
... (remaining 3128 chars omitted for brevity)

Section 2 Summary: ## 2. Check Logic

Based on description "Confirm the netlist/spef version is correct", the following items require validation:

**Validation Items**:

### 2.1 Netlist Loading Status
- **Purpose**: Verify the netlist file was successfully loaded before validating version information
- **Completeness definition**: 
  - `parsed_fields.netlist.loaded` exists AND equals `True` (or "Success")
  - `parsed_fields.netlist.source_file` exists (confirms which file was loaded)
... (remaining 3296 chars omitted for brevity)

Section 3 Summary: ## 3. Waiver Logic

Based on description "Confirm the netlist/spef version is correct", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

### 3.1 SPEF File Loading Status (Item 2.2)
... (remaining 6249 chars omitted for brevity)
</previous_sections_summary>

<!-- ========================================
     TEMPLATE: Section 4 Structure
========================================= -->

<template_section>
## 4. Implementation Guide

<!-- 
TODO: Provide practical guidance for implementation.
This section helps the Parsing Logic LLM understand where to find data and how to extract it.
-->

### 4.1 Item-Specific Implementation Points

**Data Source Inference**:
<!-- TODO: Based on description and validation needs, infer where to find the data -->
- Inferred data source: {TODO: Type of file or log}
  <!-- Example: "STA log file", "Netlist file headers", "Configuration files" -->
- Recommended file: {TODO: Typical filename or pattern}
  <!-- Example: "`sta_post_syn.log`", "`design.v`", "`*.sdc`" -->

**Information Extraction Methods**:
<!-- TODO: Suggest how to find and extract the required information -->
- **{TODO: First information category}**: {TODO: Extraction strategy}
  <!-- Example: "Search for keywords: 'Reading netlist', 'Netlist loaded'" -->
  - {TODO: Tool/source 1}: {TODO: Keywords or patterns to search}
  - {TODO: Tool/source 2}: {TODO: Keywords or patterns}
  
- **{TODO: Second information category}**: {TODO: Extraction strategy}
  - {TODO: Location}: {TODO: How to find and parse}
  <!-- Example: "File headers: Parse comments starting with '//' or '/*'" -->

**Adaptive Learning Strategy**:
<!-- TODO: Guide the Parsing Logic LLM on handling format variations -->
- Do not assume fixed formats; learn from actual file content
- Fallback handling: {TODO: What to do if information not found}
  <!-- Example: "If file not found, mark corresponding fields as missing" -->
- Error tolerance: {TODO: How to handle parsing errors}

### 4.2 Special Scenario Handling

<!-- 
TODO: Document edge cases and special scenarios based on engineering experience.
List 2-4 scenarios that might occur in practice.
-->

#### Scenario 1: {TODO: First Special Scenario Name}
<!-- Example: "SPEF Unavailable During Synthesis Stage" -->
- Check result: {TODO: Expected check outcome}
  <!-- Example: "SPEF loading status missing → missing_items" -->
- Waiver handling: {TODO: How to handle with waivers}
  <!-- Example: "If waive_items contains 'synthesis' or 'SPEF' → waive as INFO" -->

#### Scenario 2: {TODO: Second Special Scenario Name}
- Check result: {TODO: Expected outcome}
- Waiver handling: {TODO: Waiver strategy}

#### Scenario 3: {TODO: Third Special Scenario Name}
<!-- Add more scenarios as needed -->
- Check result: {TODO: Expected outcome}
- Waiver handling: {TODO: Waiver strategy}

### 4.3 Test Data Generation Guidance

**Note**: The following guidance is for generating test configurations covering all 6 test scenarios.

#### Test Scenario Matrix

Based on requirements.value and waivers.value combinations, generate 6 test scenarios:

| Scenario | requirements.value | waivers.value | Test Objective |
|----------|-------------------|---------------|----------------|
| 1 | N/A | N/A | Basic existence validation |
| 2 | N/A | 0 | Global waiver mechanism |
| 3 | N/A | >0 | Selective waiver matching mechanism |
| 4 | >0 | N/A | Pattern matching - PASS path |
| 5 | >0 | 0 | Pattern matching - FAIL path + global waiver |
| 6 | >0 | >0 | Pattern matching - FAIL path + selective waiver |

#### Inference Strategy

**Step 1: Run Parsing Logic to obtain actual metadata**

After Parsing Logic execution, analyze the actual output structure and content.

**Step 2: Extract representative keywords**

From the `value` field of parsed objects, extract characteristic keywords:
<!-- TODO: Provide guidance specific to this item -->
- {TODO: Category 1}: {TODO: Types of keywords to extract}
  <!-- Example: "Timestamps: year patterns like '2024', '2025'" -->
- {TODO: Category 2}: {TODO: Types of keywords}
  <!-- Example: "Tool names: 'Genus', 'Innovus', 'PrimeTime'" -->

**Step 3: Generate test YAML configurations**

```yaml
# Scenario 1: Basic existence check
# {ITEM_ID}_base.yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: N/A
  waive_items: []

# Scenario 2: Global waiver
# {ITEM_ID}_global_waiver.yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: 0
  waive_items: ["{TODO: Generic waiver reason}"]

# Scenario 3: Selective waiver
# {ITEM_ID}_selective_waiver.yaml
requirements:
  value: N/A
  pattern_items: []
waivers:
  value: {TODO: number of waive_items}
  waive_items:
    - "{TODO: keyword from Section 3}"
    # Add more items as needed

# Scenario 4: Pattern matching - PASS
# {ITEM_ID}_pattern_pass.yaml
requirements:
  value: {TODO: number of pattern_items}
  pattern_items:
    - "{TODO: pattern that matches actual data for first item}"
    - "{TODO: pattern that matches actual data for second item}"
    # Use "|" for OR alternatives: "keyword1|keyword2"
waivers:
  value: N/A
  waive_items: []

# Scenario 5: Pattern matching - FAIL + global waiver
# {ITEM_ID}_pattern_fail_global.yaml
requirements:
  value: {TODO: number of pattern_items}
  pattern_items:
    - "{TODO: pattern that does NOT match actual data}"
    - "{TODO: pattern that does NOT match actual data}"
waivers:
  value: 0
  waive_items: ["{TODO: global waiver reason}"]

# Scenario 6: Pattern matching - FAIL + selective waiver
# {ITEM_ID}_pattern_fail_selective.yaml
requirements:
  value: {TODO: number of pattern_items}
  pattern_items:
    - "{TODO: pattern that does NOT match}"
    - "{TODO: pattern that does NOT match}"
waivers:
  value: {TODO: number of waive_items}
  waive_items:
    - "{TODO: keyword from Section 3}"
    - "{TODO: keyword from Section 3}"
```

**Key Principles**:
1. **PASS scenarios**: Use patterns that match actual data values
2. **FAIL scenarios**: Use patterns that do NOT match actual data
3. **OR relationships**: Connect multiple keywords with `|` for higher match probability
4. **waive_items**: Reference matching keywords defined in Section 3

**Important**: These are recommendations based on Parsing Logic output. Adjust according to actual metadata structure and content.

</template_section>

<!-- ========================================
     INSTRUCTIONS: Generation Requirements
========================================= -->

<instructions>
Fill the Implementation Guide section following these requirements:

1. **Data Source Inference**: Based on previous sections, identify where to find the information
   - Infer from field types and validation requirements
   - Consider typical EDA tool outputs and log structures
   - List primary and fallback data sources

2. **Search Strategy**: Recommend practical extraction approaches
   - Keywords to search for in logs/files
   - Parsing patterns and regular expressions
   - Multi-stage extraction if needed

3. **Special Scenarios**: Document edge cases and exceptions
   - Missing file handling
   - Format variations across tools/versions
   - Fallback strategies when primary source unavailable

4. **Implementation Hints**: Practical guidance for downstream implementation
   - Common pitfalls to avoid
   - Performance considerations
   - Debugging tips

5. **Quality Check**: Ensure the complete ItemSpec meets all quality criteria
   - Semantic consistency across all sections
   - Practical implementability
   - Coverage of common scenarios
   - Adherence to framework rules

Output the complete Section 4 inside <section4></section4> tags.
</instructions>