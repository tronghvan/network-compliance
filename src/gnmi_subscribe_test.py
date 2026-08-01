from pathlib import Path
from pygnmi.client import gNMIclient
import json
import yaml
import re
import time
import threading


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = BASE_DIR / "inventory" / "inventory.yml"
DEFAULT_RULES_DIR = BASE_DIR / "rules"

def load_inventory(path=DEFAULT_INVENTORY):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("devices", [])

def load_event_rules(path=DEFAULT_RULES_DIR):
    all_rules = []
    rules_path = Path(path)
    if not rules_path.exists():
        fallback_file = BASE_DIR / "legacy-rules" / "golden-config-rules-event.yml"
        with open(fallback_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f).get("rules", [])
            
    for file_path in rules_path.glob("*.yml"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "rules" in data:
                all_rules.extend(data["rules"])
    return all_rules

def check_event_against_rules(path, val, rules):
    
    results = []

    for rule in rules:
        rule_groups = rule.get("metadata", {}).get("applies_to", {}).get("device_group")

        if rule_group != dev_group:
            continue 
        if rule.get("path_contains") and rule["path_contains"] not in path:
            continue  

        if "expected_value_contains" in rule:
            match = re.search(r"host=([\d.]+)", path)
            actual_host = match.group(1) if match else None

            if actual_host != rule["expected_value_contains"]:
                results.append({
                    "severity": rule["severity"],
                    "message": f"{rule['name']} actual value: {actual_host}, expectation: {rule['expected_value_contains']}"
                })
            else:
                results.append({
                    "severity": "ok",
                    "message": f"{rule['name']} OK, used address {actual_host}"
                })

        elif "expected_field" in rule:
            field_name = rule["expected_field"]
            actual_value = val.get(field_name) if isinstance(val, dict) else None
            expected_value = rule["expected_value"]

            if actual_value != expected_value:
                results.append({
                    "severity": rule["severity"],
                    "message": f"{rule['name']}  {field_name} reality: {actual_value}, expectation: {expected_value}"
                })
            else:
                results.append({
                    "severity": "ok",
                    "message": f"{rule['name']} OK, {field_name}={actual_value}"
                })

    return results


def gnmi_listener(device_conf, device_name, dev_group, rules):
    try:
        with gNMIclient(**device_conf) as gc:
            print(f"[{device_name}] Sign up to listen on  /system/logging...")
            subscription = gc.subscribe2(
                subscribe={
                    "subscription": [{"path": "/system/logging", "mode": "on_change"}],
                    "mode": "stream",
                    "encoding": "json_ietf"
                }
            )

            sync_completed = False
            for update in subscription:
                if update.get("sync_response"):
                    sync_completed = True
                    print(f"[{device_name}] The circuit is complete. I'm really listening now....")
                    continue
                if not sync_completed:
                    continue

                update_data = update.get("update", {})
                for change in update_data.get("update", []):
                    path = change.get("path", "")
                    val = change.get("val", {})

                    results = check_event_against_rules(path, val, rules)
                    if not results:
                        continue

                    print(f"\nEvent about {device_name} (Group: {dev_group})")
                    print(f"Path: {path}")
                    for r in results:
                        tag = r["severity"].upper()
                        print(f"[{tag}] {r['message']}")
                        
    except Exception as e:
        print(f"[!] gNMI connection error {device_name}: {e}")


def main():
    devices = load_inventory()
    rules = load_event_rules()

    if not devices:
        print("[!] No devices found in inventory.yml!")
        return

    print(f"Downloaded successfully {len(devices)} devices. Initiate a listener flow....\n")

    listener_threads = []
    for dev in devices:
        device_name = dev["name"]
        dev_group = dev.get("group", "default")
        device_conf = {
            "target": (dev["host"], 57400),
            "username": dev["username"],
            "password": dev["password"],
            "ssl": dev["ssl"],
        }

        t = threading.Thread(
            target=gnmi_listener, 
            args=(device_conf, device_name, dev_group, rules), 
            daemon=True
        )
        t.start()
        listener_threads.append(t)

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStop program! Test successful.")

if __name__ == "__main__":
    main()

