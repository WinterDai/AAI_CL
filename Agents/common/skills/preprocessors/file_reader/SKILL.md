---
name: file_reader
version: 1.0.0
type: preprocessor
description: Read input files and extract sample lines for LLM analysis
owner:
  - ContextAgent
inputs:
  file_paths:
    type: list[str]
    description: List of file paths to read
  lines_per_file:
    type: int
    default: 100
    description: Number of lines to read from each file
outputs:
  file_analysis:
    type: FileAnalysis
    description: File analysis result with samples and format detection
dependencies:
  - models.FileAnalysis
  - models.PatternMatch
---

# File Reader Preprocessor

## Purpose

Read input files and extract sample lines for LLM to perform semantic analysis. This preprocessor only extracts raw data - it does NOT understand the content.

## Key Functions

```python
def read_files(file_paths: list[str], lines_per_file: int = 100) -> FileAnalysis
```

## Responsibilities (Pure Data Extraction)

✅ **Does**:
- Read first N lines from each file
- Detect file format (log/report/csv/json/custom)
- Extract representative sample lines
- Count total lines sampled

❌ **Does NOT** (Leave to LLM):
- Understand data meaning
- Design parsing logic
- Choose regex patterns
- Determine what to check

## Format Detection Rules

| Format | Detection Criteria |
|--------|-------------------|
| json | Starts with `{` or `[` |
| csv | Multiple lines with 2+ commas |
| log | Contains ERROR/WARN/INFO/DEBUG or timestamps |
| report | Contains separators (===, ---) or "Report"/"Summary" |
| custom | Default fallback |

## Output Schema

```python
@dataclass
class FileAnalysis:
    files_analyzed: int
    total_lines_sampled: int
    detected_format: str  # log/report/csv/json/custom
    common_patterns: list[PatternMatch]  # Auxiliary info
    section_headers: list[str]  # Detected headers
    sample_lines: list[str]  # Representative samples for LLM
```

## Usage Example

```python
from agents.common.skills.preprocessors.file_reader import read_files

analysis = read_files(["/path/to/timing.rpt"], lines_per_file=100)
print(f"Format: {analysis.detected_format}")  # Format: report
print(f"Samples: {len(analysis.sample_lines)}")  # Samples: 20
```

## Semantic Understanding Flow

```
file_reader (Preprocessor)     →     LLM Phase
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extracts sample_lines         →     Understands meaning
Detects format                →     Designs check_logic
Counts files                  →     Generates regex patterns
```
