## 1. Parsing Logic

**Information to Extract**:

### 1.1 Netlist File Information
- **Purpose**: Extract version metadata from netlist files to verify tool, version, and generation timestamp information
- **Key Fields**:
  - `loaded`: Boolean indicating whether netlist file was successfully accessed and parsed
  - `tool_name`: String representing the EDA tool that generated the netlist (e.g., "Innovus", "Genus", "ICC2", "DC")
  - `tool_version`: String representing the tool version number (e.g., "21.1", "2023.03-SP2")
  - `timestamp`: String representing the generation date/time of the netlist
  - `format`: String representing the netlist format (e.g., "Verilog", "VHDL", "DEF")

### 1.2 SPEF File Information
- **Purpose**: Extract version metadata from SPEF (Standard Parasitic Exchange Format) files to verify extraction tool, version, standard compliance, and generation timestamp
- **Key Fields**:
  - `loaded`: Boolean indicating whether SPEF file was successfully accessed and parsed
  - `tool_name`: String representing the parasitic extraction tool (e.g., "StarRC", "Quantus", "PrimeTime")
  - `tool_version`: String representing the extraction tool version number
  - `timestamp`: String representing the generation date/time of the SPEF file
  - `standard_version`: String representing the IEEE standard version (e.g., "IEEE 1481-1999", "IEEE 1481-2009")

### 1.3 File Metadata
- **Purpose**: Provide traceability information for debugging and audit purposes
- **Key Fields**:
  - `source_file`: Absolute path to the input file where information was extracted
  - `line_number`: Line number where version information was found
  - `matched_content`: The actual text line that was matched during extraction

**Data Structure**: Output structure follows global_rules.md Section 2.4.1 (Required metadata + parsed_fields)

**parsed_fields Example**:
```python
{
  "netlist": {
    "loaded": True,
    "tool_name": "Innovus",
    "tool_version": "21.10-s080_1",
    "timestamp": "2025-01-15 14:23:45",
    "format": "Verilog"
  },
  "spef": {
    "loaded": True,
    "tool_name": "StarRC",
    "tool_version": "2022.06-SP1",
    "timestamp": "2025-01-15 16:45:12",
    "standard_version": "IEEE 1481-2009"
  }
}
```

**Complete Output Structure Example**:
```python
[
  {
    "value": "Netlist version: Innovus 21.10-s080_1",
    "source_file": "/project/design/netlist/top.v.gz",
    "line_number": 3,
    "matched_content": "// Generator: Cadence Innovus 21.10-s080_1",
    "parsed_fields": {
      "netlist": {
        "loaded": True,
        "tool_name": "Innovus",
        "tool_version": "21.10-s080_1",
        "timestamp": "2025-01-15 14:23:45",
        "format": "Verilog"
      }
    }
  },
  {
    "value": "SPEF version: IEEE 1481-2009",
    "source_file": "/project/design/spef/top.spef.gz",
    "line_number": 1,
    "matched_content": "*SPEF \"IEEE 1481-2009\"",
    "parsed_fields": {
      "spef": {
        "loaded": True,
        "tool_name": "StarRC",
        "tool_version": "2022.06-SP1",
        "timestamp": "2025-01-15 16:45:12",
        "standard_version": "IEEE 1481-2009"
      }
    }
  }
]
```