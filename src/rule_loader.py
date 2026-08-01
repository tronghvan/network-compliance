import os
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RULES_DIR = BASE_DIR / "rules"

def load_all_rules(rules_dir=DEFAULT_RULES_DIR):

    all_rules = []
    for filename in os.listdir(rules_dir):
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            filepath = os.path.join(rules_dir, filename)
            with open(filepath, "r") as f:
                rule = yaml.safe_load(f)
                rule["_source_file"] = filename
                all_rules.append(rule)
    return all_rules

def get_rules_for_device(device, all_rules):
   
    device_group = device.get("group")
    applicable_rules = []

    for rule in all_rules:
        rule_group = rule.get("metadata", {}).get("applies_to", {}).get("device_group")
        if rule_group == device_group:
            applicable_rules.append(rule)

    return applicable_rules

def print_rule_summary(all_rules):
    
    print("\nExisting rule list")
    for rule in all_rules:
        meta = rule.get("metadata", {})
        print(f"[{meta.get('rule_id')}] {meta.get('name')}")
        print(f"    Created by: {meta.get('created_by')} | Version: {meta.get('version')}")
        print(f"    Apply to groups: {meta.get('applies_to', {}).get('device_group')}")
        print(f"    Level: {rule.get('severity')} | Tu dong sua: {rule.get('auto_remediate')}")
        print(f"    Source files: {rule.get('_source_file')}\n")

if __name__ == "__main__":
    rules = load_all_rules()
    print_rule_summary(rules)
