## 3. Waiver Logic

Based on description "Confirm the netlist/spef version is correct", analyze waiver scenarios for validation items:

**Waivable Items and Matching Keywords**:

### 3.1 SPEF File Loading Status (Item 2.2)
- **Waiver scenario**: During synthesis or early design stages, SPEF files are not yet available because parasitic extraction occurs during placement and routing phases. Running timing analysis without parasitics (ideal/zero-parasitic mode) is a valid early-stage verification approach.
- **Typical waiver reason**: "SPEF not required at synthesis stage - pre-layout timing analysis" OR "Zero-parasitic analysis mode for early timing checks"
- **Matching keywords**: 
  - `"SPEF"` + `"synthesis"` (stage-based waiver)
  - `"SPEF"` + `"pre-layout"` (stage-based waiver)
  - `"SPEF"` + `"ideal"` (analysis mode waiver)
  - `"SPEF"` + `"zero parasitic"` (analysis mode waiver)
- **Business justification**: Early design stages focus on logical correctness and rough timing estimates; parasitic data is not available until physical implementation

### 3.2 SPEF Version Completeness (Item 2.4)
- **Waiver scenario**: When SPEF loading is waived (synthesis stage), version validation becomes irrelevant. Additionally, legacy SPEF files from older extraction tools may lack embedded version metadata but are still valid for regression testing against golden references.
- **Typical waiver reason**: "SPEF version check waived - synthesis stage" OR "Legacy SPEF format without version metadata - verified externally"
- **Matching keywords**:
  - `"SPEF"` + `"version"` + `"synthesis"` (stage-based waiver)
  - `"SPEF"` + `"version"` + `"legacy"` (format-based waiver)
  - `"SPEF"` + `"version"` + `"golden"` (regression testing waiver)
  - `"SPEF"` + `"version"` + `"historical"` (regression testing waiver)
- **Business justification**: Version metadata may be unavailable in legacy formats or irrelevant when SPEF itself is not required; external verification processes ensure correctness

### 3.3 Netlist Version Completeness (Item 2.3)
- **Waiver scenario**: Legacy netlist formats (e.g., older Verilog netlists, third-party IP blocks) may not contain embedded tool version information. These netlists are still functionally correct but lack metadata. Additionally, during regression testing, golden netlists from previous releases may have different version formats.
- **Typical waiver reason**: "Legacy netlist format - version verified through external documentation" OR "Golden netlist from regression suite - version tracking external"
- **Matching keywords**:
  - `"netlist"` + `"version"` + `"legacy"` (format-based waiver)
  - `"netlist"` + `"version"` + `"golden"` (regression testing waiver)
  - `"netlist"` + `"version"` + `"third-party"` (IP integration waiver)
  - `"netlist"` + `"version"` + `"vendor IP"` (IP integration waiver)
- **Business justification**: Older netlist formats or third-party IP may not follow current version metadata standards; correctness is verified through alternative means (documentation, regression results)

### 3.4 Tool Version Mismatch
- **Waiver scenario**: Incremental design flows may re-run only parasitic extraction with a newer tool version while keeping the original netlist. This intentional version mismatch is acceptable if tool compatibility has been verified. Similarly, tool upgrades mid-project may result in mixed versions across design artifacts.
- **Typical waiver reason**: "Intentional tool version mismatch - incremental extraction flow with verified compatibility" OR "Tool upgrade mid-project - version compatibility confirmed"
- **Matching keywords**:
  - `"version"` + `"mismatch"` + `"incremental"` (flow-based waiver)
  - `"version"` + `"mismatch"` + `"re-extraction"` (flow-based waiver)
  - `"version"` + `"upgrade"` + `"compatible"` (tool upgrade waiver)
  - `"version"` + `"mixed"` + `"verified"` (tool upgrade waiver)
- **Business justification**: Incremental flows optimize runtime by re-running only necessary steps; tool compatibility testing ensures mixed versions produce valid results

---

**Waiver Modes**:

- **Global Waiver Mode** (`waivers.value = 0`):
  - **Behavior**: All validation items (2.1, 2.2, 2.3, 2.4) are waived regardless of failure reasons
  - **Use cases**: 
    - Early development phases where version tracking is not yet enforced
    - Experimental runs where version correctness is not critical
    - Quick sanity checks bypassing formal validation
  - **Traceability**: Global waiver reason must be documented in `waivers.reason` field

- **Selective Waiver Mode** (`waivers.value > 0`, `waivers.waive_items` configured):
  - **Behavior**: Only validation items matching keywords in `waivers.waive_items` are waived
  - **Matching strategy**: 
    - Keyword matching is case-insensitive
    - Multiple keywords in a waive_item entry use AND logic (all must match)
    - Multiple waive_item entries use OR logic (any entry can trigger waiver)
    - Example: `waive_items = [["SPEF", "synthesis"], ["netlist", "legacy"]]` waives SPEF checks at synthesis OR netlist checks for legacy formats
  - **Application**: Targeted waivers for specific known issues while maintaining validation for other items
  - **Traceability**: Each waived item must have corresponding entry in `waivers.waive_items` with clear keyword justification

**Implementation Guidance**:

- **Pattern Matching Strategy**:
  - Use exact keyword matching for high-confidence waivers (e.g., "synthesis", "legacy")
  - Support wildcard patterns for tool version variations (e.g., "Genus 21.*" matches "Genus 21.1", "Genus 21.2")
  - Consider regex support for complex version patterns if needed by project requirements

- **Linking Waivers to Validation Items**:
  - Item 2.2 (SPEF Loading) ↔ Keywords containing "SPEF" + stage/mode indicators
  - Item 2.4 (SPEF Version) ↔ Keywords containing "SPEF" + "version" + justification
  - Item 2.3 (Netlist Version) ↔ Keywords containing "netlist" + "version" + justification
  - Item 2.1 (Netlist Loading) ↔ Generally not waivable (netlist is mandatory for all flows)

- **Traceability Requirements**:
  - All waivers must include `waivers.reason` field explaining business justification
  - Waiver decisions must be logged with timestamp and approver information
  - Selective waivers must document which specific validation items were waived and why
  - Waiver audit trail should link to design stage, tool versions, and project phase