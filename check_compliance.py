#!/usr/bin/env python3
import yaml

def load_rules(path="golden-config-rules.yml"):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data["rules"]

def load_inventory(path="inventory.yml"):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data["devices"]

def check_device_compliance(device_name, config_text, rules):
    violations = []
    for rule in rules:
        if rule["check"] not in config_text:
            violations.append({
                "device": device_name,
                "rule": rule["name"],
                "severity": rule["severity"]
            })
    return violations


def main():
    rules = load_rules()
    devices = load_inventory()
    all_violations = []
    missing_file = []
    for device in devices:
        filename = f"configs_actual_{device['name']}.txt"
        try:
            with open(filename, "r") as f:
                 config_text = f.read()
        except FileNotFoundError:
            print(f"Warning findn't file config {device['name']}")
            missing_file.append(device["name"])
        violations = check_device_compliance(device["name"], config_text, rules)
        all_violations.extend(violations)
    print("\n ouput")
    if missing_file:
        print(f"no check devices : {', '.join(missing_file)}")

    if not all_violations and not missing_file:
        print("All oke")
    elif all_violations:
        for v in all_violations:
            print(f"[{v['security'].upper()}] Thiet bi '{v['device']}' vi pham quy tac: \"{v['rule']}\"")
    if missing_file:
        exit(1) 
    return all_violations
if __name__ == "__main__":
    main()
