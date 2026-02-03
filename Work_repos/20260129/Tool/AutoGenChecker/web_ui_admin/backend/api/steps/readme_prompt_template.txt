Generate a comprehensive README.md following AutoGenChecker standard format.

Use the file analysis to fill ALL sections completely - no TODOs in final output.

The README MUST follow this EXACT structure (see IMP-7-0-0-00_README.md for reference):

1. # {item_id}: {description} header
2. ## Overview section (Check ID, Description, Category, Input Files, functional description)
3. ## Check Logic section (Input Parsing with Key Patterns, Detection Logic steps)
4. ## Output Behavior section (existence_check vs status_check modes)
5. ## Output Descriptions section (complete Python constants for Type 1/2/3/4)
6. ### INFO01/ERROR01 Display Format
7. ## Type 1: Boolean Check (with sample YAML + outputs)
8. ### Type 1 Variant: waivers.value=0 (Forced PASS Mode)
9. ## Type 2: Value Check (with sample YAML + outputs)
10. ### Type 2 Variant: waivers.value=0 (Forced PASS Mode)
11. ## Type 3: Value Check with Waiver Logic
12. ## Type 4: Boolean Check with Waiver Logic

CRITICAL: Fill pattern1 regex with REAL patterns from file analysis, not placeholders!
