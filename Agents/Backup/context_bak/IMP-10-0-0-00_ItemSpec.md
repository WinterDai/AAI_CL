# ItemSpec: {ITEM_ID}

<!-- TODO: Replace {ITEM_ID} with actual item identifier -->

## 1. Parsing Logic

<!-- 
TODO: Define what information to extract based on the description.
Guidelines:
- Identify key entities from the description (e.g., files, versions, configurations)
- List typical fields based on EDA industry standards
- Design parsed_fields structure for checker-specific data
- Reference: global_rules.md Section 2.4.1 for data structure requirements
-->

**Information to Extract**:

### 1.1 {TODO: First Information Category}
<!-- Example: "Netlist File Information", "Clock Configuration", "Timing Constraints" -->
- **Purpose**: {TODO: Why extract this information}
- **Key Fields**:
  - {TODO: Field 1 - describe what it represents}
  - {TODO: Field 2 - describe what it represents}
  - {TODO: Field 3 - describe what it represents}
  - {TODO: Add more fields as needed}

### 1.2 {TODO: Second Information Category}
<!-- Add more subsections (1.3, 1.4, etc.) as needed for different information categories -->
- **Purpose**: {TODO: Why extract this information}
- **Key Fields**:
  - {TODO: Field 1}
  - {TODO: Field 2}
  - {TODO: Field 3}

**Data Structure**: Output structure follows global_rules.md Section 2.4.1 (Required metadata + parsed_fields)

**parsed_fields Example**:
```python
{
  # TODO: Design the structure based on above fields
  # Example structure:
  "{category_1}": {
    "{field_name}": "...",
    "{field_name}": "...",
  },
  "{category_2}": {
    "{field_name}": "...",
    "{field_name}": "...",
  }
}
```

---

## 2. Check Logic

<!-- 
TODO: Define what to verify based on the description.
Guidelines:
- Determine validation items (typically 2-6 items)
- Define completeness criteria for each item
- Decide which items need pattern matching vs. existence checks
- Specify pattern_items correspondence for items requiring pattern matching
- Reference: global_rules.md Section 2.2 for check logic rules
-->

Based on description "{DESCRIPTION}", the following items require validation:

**Validation Items**:

1. **{TODO: First Validation Item Name}**
   <!-- Example: "Netlist File Loading Status", "Clock Frequency Constraints" -->
   - Completeness definition: {TODO: What makes this item complete/valid}
   <!-- Example: "parsed_fields.netlist.file_path exists AND loaded=True" -->

2. **{TODO: Second Validation Item Name}**
   - Completeness definition: {TODO: Define validation criteria}

3. **{TODO: Third Validation Item Name}**
   <!-- Add more items as needed -->
   - Completeness definition: {TODO: Define validation criteria}

**Pattern Matching** (when requirements.pattern_items > 0):
<!-- TODO: Specify which items require pattern matching -->
- Items requiring pattern matching: {TODO: List item numbers, e.g., "Item 2, Item 4"}
- Items with existence check only: {TODO: List item numbers, e.g., "Item 1, Item 3"}

**Pattern Correspondence Order** (follows global_rules.md pattern_items rules):
<!-- TODO: Define the mapping between pattern_items array indices and validation items -->
- `pattern_items[0]` → {TODO: Item number and name}
- `pattern_items[1]` → {TODO: Item number and name}
<!-- Add more mappings as needed for all items requiring pattern matching -->

**Note**: Each pattern_item can use `|` to separate multiple alternative patterns (OR relationship).

---

## 3. Waiver Logic

<!-- 
TODO: Define scenarios where validation failures are acceptable.
Guidelines:
- Think about different design stages and when checks might legitimately fail
- Consider testing scenarios (golden files, regression testing)
- List 2-4 common waiver scenarios based on engineering experience
- Provide concrete waiver reasons and matching keywords
- Reference: global_rules.md Section 2.3 for waiver logic rules
-->

Based on description "{DESCRIPTION}", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

1. **{TODO: First Waivable Item}**
   <!-- Example: "SPEF File Loading Status" -->
   - Waiver scenario: {TODO: Describe when this failure is acceptable}
   <!-- Example: "Synthesis stage does not require SPEF files" -->
   - Typical waiver reason: {TODO: Provide example reason text}
   <!-- Example: "Current stage is synthesis, SPEF check not applicable" -->
   - Matching keywords: {TODO: List keywords for selective waiver matching}
   <!-- Example: "SPEF", "synthesis" -->

2. **{TODO: Second Waivable Item}**
   - Waiver scenario: {TODO: Describe acceptable failure scenario}
   - Typical waiver reason: {TODO: Example reason}
   - Matching keywords: {TODO: Keywords}

3. **{TODO: Third Waivable Item}**
   <!-- Add more waivable items as needed (typically 2-4 items) -->
   - Waiver scenario: {TODO: Scenario description}
   - Typical waiver reason: {TODO: Example reason}
   - Matching keywords: {TODO: Keywords}

---

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
