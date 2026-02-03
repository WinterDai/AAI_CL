<section1>
## 1. Parsing Logic

**Information to Extract**:

### 1.1 Netlist File Information
- **Purpose**: Extract netlist loading status and version metadata to verify the netlist file was successfully read and contains complete version information
- **Key Fields**:
  - `loaded`: Boolean or status string indicating whether the netlist was successfully loaded (e.g., "Success", "Failed", True/False)
  - `tool_name`: String representing the synthesis/netlist generation tool (e.g., "Genus", "Design Compiler", "Innovus")
  - `version`: String representing the tool version number (e.g., "21.1", "2023.03-SP1")
  - `timestamp`: String representing the netlist generation timestamp (ISO format preferred, or tool-specific format)
  - `source_file`: String containing the path to the netlist file that was parsed (metadata for traceability)

### 1.2 SPEF File Information
- **Purpose**: Extract SPEF loading status and version metadata to verify the parasitic file was successfully read and contains complete version information
- **Key Fields**:
  - `loaded`: Boolean or status string indicating whether the SPEF was successfully loaded (e.g., "Success", "Failed", True/False)
  - `tool_name`: String representing the parasitic extraction tool (e.g., "Innovus", "ICC2", "StarRC", "Quantus")
  - `version`: String representing the tool version number (e.g., "21.1", "2022.06")
  - `timestamp`: String representing the SPEF generation timestamp (ISO format preferred, or tool-specific format)
  - `source_file`: String containing the path to the SPEF file that was parsed (metadata for traceability)

### 1.3 Extraction Metadata
- **Purpose**: Provide traceability information about when and where the parsing occurred
- **Key Fields**:
  - `extraction_timestamp`: String representing when the parsing logic extracted this information (ISO 8601 format recommended)
  - `log_file_path`: String containing the absolute path to the log file or input file being parsed

**Data Structure**: Output structure follows global_rules.md Section 2.4.1 (Required metadata + parsed_fields)

**parsed_fields Example**:
```python
{
  "netlist": {
    "loaded": True,  # or "Success"
    "tool_name": "Genus",
    "version": "21.1-s100",
    "timestamp": "2025-01-15T14:30:00",
    "source_file": "/project/design/netlist/top.v.gz"
  },
  "spef": {
    "loaded": True,  # or "Success"
    "tool_name": "Innovus",
    "version": "21.1",
    "timestamp": "2025-01-15T16:45:00",
    "source_file": "/project/design/spef/top.spef.gz"
  },
  "metadata": {
    "extraction_timestamp": "2025-01-16T09:00:00",
    "log_file_path": "/project/logs/sta_run.log"
  }
}
```

**Complete Output Structure Example**:
```python
[
  {
    "value": "Netlist: Genus 21.1-s100, SPEF: Innovus 21.1",
    "source_file": "/project/logs/sta_run.log",
    "line_number": 42,
    "matched_content": "Reading netlist from /project/design/netlist/top.v.gz (Genus 21.1-s100)",
    "parsed_fields": {
      "netlist": {
        "loaded": True,
        "tool_name": "Genus",
        "version": "21.1-s100",
        "timestamp": "2025-01-15T14:30:00",
        "source_file": "/project/design/netlist/top.v.gz"
      },
      "spef": {
        "loaded": True,
        "tool_name": "Innovus",
        "version": "21.1",
        "timestamp": "2025-01-15T16:45:00",
        "source_file": "/project/design/spef/top.spef.gz"
      },
      "metadata": {
        "extraction_timestamp": "2025-01-16T09:00:00",
        "log_file_path": "/project/logs/sta_run.log"
      }
    }
  }
]
```

</section1>