## 3. Waiver Logic

Based on description "Confirm the netlist/spef version is correct", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

### 3.1 SPEF File Loading Status (Item 2.3)
- **Waiver scenario**: Early design stages where parasitic extraction has not yet been performed
  - Synthesis stage: Only netlist exists, SPEF generation occurs later in P&R flow
  - Pre-layout timing analysis: Using wireload models instead of extracted parasitics
  - Floorplanning stage: Physical design not finalized for extraction
- **Typical waiver reason**: "Pre-extraction design stage - SPEF file not yet available. Using wireload models for timing analysis."
- **Matching keywords**: `"SPEF"`, `"synthesis"`, `"pre-extraction"`, `"wireload"`, `"early-stage"`, `"floorplan"`
- **Business justification**: SPEF files are only generated after place-and-route completion. Earlier design stages legitimately operate without parasitic data.

### 3.2 SPEF Version Completeness (Item 2.4)
- **Waiver scenario**: Legacy or third-party SPEF files with non-standard headers
  - Regression testing: Golden reference files from previous tool versions may lack complete metadata
  - Vendor-provided IP blocks: SPEF files may use proprietary header formats
  - Format conversion: SPEF files converted from other formats may have incomplete version information
- **Typical waiver reason**: "Legacy SPEF file from regression suite - version metadata grandfathered for compatibility"
- **Matching keywords**: `"SPEF"`, `"legacy"`, `"golden"`, `"regression"`, `"vendor"`, `"third-party"`, `"converted"`
- **Business justification**: Historical data used for validation may predate current version tracking requirements. Functional correctness takes precedence over metadata completeness.

### 3.3 Netlist Version Completeness (Item 2.2)
- **Waiver scenario**: Hand-edited or merged netlists lacking tool-generated headers
  - ECO (Engineering Change Order) flows: Manual netlist modifications for bug fixes
  - Netlist merging: Combining multiple sub-netlists may strip original headers
  - Custom scripting: Automated netlist transformations may not preserve version comments
- **Typical waiver reason**: "ECO-modified netlist - original tool version information removed during manual editing"
- **Matching keywords**: `"netlist"`, `"ECO"`, `"manual"`, `"hand-edit"`, `"merged"`, `"custom"`
- **Business justification**: Engineering change orders require direct netlist modification. Version tracking shifts to ECO documentation rather than file headers.

### 3.4 Both Netlist and SPEF Version Information (Items 2.2 and 2.4)
- **Waiver scenario**: Ideal/academic test cases without real tool provenance
  - Benchmark circuits: Standard test designs (ISCAS, ITC) without tool metadata
  - Simulation-only flows: Behavioral models not requiring production tool versions
  - Algorithm validation: Synthetic test cases for checker development
- **Typical waiver reason**: "Academic benchmark circuit - no production tool version information available"
- **Matching keywords**: `"benchmark"`, `"test"`, `"simulation"`, `"academic"`, `"synthetic"`, `"ISCAS"`, `"ITC"`
- **Business justification**: Research and development activities use standardized test cases that lack production tool metadata but serve valid verification purposes.

---

**Waiver Modes**:

### Global Waiver Mode (waivers.value = 0)
- **Behavior**: All validation items (2.1, 2.2, 2.3, 2.4) are waived unconditionally
- **Use cases**:
  - Initial checker deployment: Gradual rollout without breaking existing flows
  - Tool migration periods: Transitioning between EDA tool versions
  - Emergency bypass: Critical tapeout schedules requiring temporary relaxation
- **Application**: Set `waivers.value = 0` in configuration
- **Traceability**: Global waiver reason must be documented in `waivers.waive_reasons[0]`

### Selective Waiver Mode (waivers.value > 0)
- **Behavior**: Only validation items matching keywords in `waivers.waive_items` are waived
- **Matching strategy**:
  - **Exact matching**: Item identifier must exactly match waive_items entry
    - Example: `waive_items = ["2.3"]` waives only SPEF loading status
  - **Keyword matching**: Waive_items entries matched against scenario keywords
    - Example: `waive_items = ["SPEF", "synthesis"]` waives items 2.3 and 2.4 in synthesis context
  - **Wildcard matching**: Use `"*"` for pattern-based matching
    - Example: `waive_items = ["SPEF*"]` waives all SPEF-related items (2.3, 2.4)
- **Application**: 
  - Set `waivers.value = N` where N = number of items in `waivers.waive_items`
  - Populate `waivers.waive_items` with item identifiers or keywords
  - Provide corresponding reasons in `waivers.waive_reasons`
- **Traceability**: Each waived item must have corresponding entry in waive_reasons at same index

**Implementation Guidance**:

1. **Waiver-to-Item Mapping**:
   - Item 2.1 (Netlist loading): Rarely waived - indicates fundamental file access problem
   - Item 2.2 (Netlist version): Waivable via keywords `"netlist"`, `"ECO"`, `"manual"`, `"benchmark"`
   - Item 2.3 (SPEF loading): Waivable via keywords `"SPEF"`, `"synthesis"`, `"pre-extraction"`
   - Item 2.4 (SPEF version): Waivable via keywords `"SPEF"`, `"legacy"`, `"vendor"`

2. **Keyword Matching Logic**:
   ```python
   # Pseudo-code for selective waiver matching
   for validation_item in failed_items:
       item_id = validation_item.id  # e.g., "2.3"
       item_keywords = validation_item.keywords  # e.g., ["SPEF", "loading"]
       
       for waive_entry in waivers.waive_items:
           if waive_entry == item_id:  # Exact match
               apply_waiver(validation_item)
           elif any(keyword in waive_entry for keyword in item_keywords):  # Keyword match
               apply_waiver(validation_item)
   ```

3. **Traceability Requirements**:
   - Each waiver must reference specific validation item(s) by ID
   - Waiver reason must include business justification and approver information
   - Waiver application must be logged with timestamp and user context
   - Audit trail must link waived failures to original check results

4. **Best Practices**:
   - Prefer selective waivers over global waivers for better traceability
   - Document waiver expiration conditions (e.g., "valid until P&R completion")
   - Review and refresh waivers periodically (recommend quarterly)
   - Escalate repeated waivers as potential flow issues requiring root cause analysis