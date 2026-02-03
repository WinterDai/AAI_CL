import csv
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path
import yaml

# Load checklist items
def parse_checklist(checklist_csv):
    sections = OrderedDict()
    with open(checklist_csv, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            module = row['Check_modules'].strip()
            item = row['Item'].strip()
            info = row['Info'].strip()
            if module not in sections:
                sections[module] = {'checklist_item': [], 'prompt_item': []}
            sections[module]['checklist_item'].append(OrderedDict([(item, info)]))
    return sections

# Load prompt items and group them by module
def load_prompt_items_grouped(prompt_csv):
    module_prompts = defaultdict(list)
    if not prompt_csv.exists():
        return module_prompts
    with open(prompt_csv, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            module = row.get('Check_modules', '').strip()
            name = row.get('Item', '').strip()
            info = row.get('Info', '').strip()
            if module and name and info:
                module_prompts[module].append(OrderedDict([(name, info)]))
    return module_prompts

# Write YAML output
def write_yaml(out_yaml, sections):
    with out_yaml.open('w', encoding='utf-8') as f:
        yaml.dump(sections, f, default_flow_style=False, allow_unicode=True)

# Main execution
checklist_csv = Path("CheckList.csv")
prompt_csv = Path("promp_item.csv")
out_yaml = Path("CheckList_Index.yaml")

sections = parse_checklist(checklist_csv)
module_prompts = load_prompt_items_grouped(prompt_csv)

# Assign prompt items to each section based on module name
for module in sections:
    if module in module_prompts:
        sections[module]['prompt_item'] = module_prompts[module]
    else:
        sections[module]['prompt_item'] = []

write_yaml(out_yaml, sections)

# Summary
total_items = sum(len(sec["checklist_item"]) for sec in sections.values())
total_prompts = sum(len(sec["prompt_item"]) for sec in sections.values())
print("Generated:", out_yaml)
print("Checklist items:", total_items)
print("Prompt items (total):", total_prompts)
