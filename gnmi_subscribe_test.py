from pygnmi.client import gNMIclient
import json
import yaml
import re

def load_event_rules(path="golden-config-rules-event.yml"):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data["rules"]

def check_event_against_rules(path, val, rules):
    
    results = []

    for rule in rules:
        # Buoc 1: kiem tra su kien nay co lien quan toi rule khong
        if rule.get("path_contains") and rule["path_contains"] not in path:
            continue  # Rule nay khong lien quan toi su kien nay, bo qua

        # Buoc 2: neu lien quan, kiem tra gia tri co dung khong
        if "expected_value_contains" in rule:
            # Vi du: host trong path phai la 10.0.0.100
            match = re.search(r"host=([\d.]+)", path)
            actual_host = match.group(1) if match else None

            if actual_host != rule["expected_value_contains"]:
                results.append({
                    "severity": rule["severity"],
                    "message": f"{rule['name']} -- gia tri thuc te: {actual_host}, mong doi: {rule['expected_value_contains']}"
                })
            else:
                results.append({
                    "severity": "ok",
                    "message": f"{rule['name']} -- OK, dung dia chi {actual_host}"
                })

        elif "expected_field" in rule:
            field_name = rule["expected_field"]
            actual_value = val.get(field_name) if isinstance(val, dict) else None
            expected_value = rule["expected_value"]

            if actual_value != expected_value:
                results.append({
                    "severity": rule["severity"],
                    "message": f"{rule['name']} -- {field_name} thuc te: {actual_value}, mong doi: {expected_value}"
                })
            else:
                results.append({
                    "severity": "ok",
                    "message": f"{rule['name']} -- OK, {field_name}={actual_value}"
                })

    return results

def handle_update(update, device_name, rules):
    update_data = update.get("update", {})
    changes = update_data.get("update", [])

    for change in changes:
        path = change.get("path", "")
        val = change.get("val", {})

        results = check_event_against_rules(path, val, rules)

        if not results:
            # Khong co rule nao lien quan toi su kien nay, bo qua im lang
            continue

        print(f"\n--- Su kien tren {device_name} ---")
        print(f"Path: {path}")
        for r in results:
            tag = r["severity"].upper()
            print(f"[{tag}] {r['message']}")

def main():
    device_name = "router3"
    rules = load_event_rules()

    device = {
        "target": ("172.20.20.3", 57400),
        "username": "admin",
        "password": "NokiaSrl1!",
        "ssl": True,
    }

    subscribe_path = ["/system/logging"]

    with gNMIclient(**device) as gc:
        print("Da dang ky lang nghe thay doi tren /system/logging")
        print("Dang dong bo trang thai ban dau...\n")

        subscription = gc.subscribe2(
            subscribe={
                "subscription": [{"path": p, "mode": "on_change"} for p in subscribe_path],
                "mode": "stream",
                "encoding": "json_ietf"
            }
        )

        sync_completed = False

        for update in subscription:
            if update.get("sync_response"):
                sync_completed = True
                print(">>> Da dong bo xong. Bat dau lang nghe thay doi THAT SU...\n")
                continue

            if not sync_completed:
                continue

            handle_update(update, device_name, rules)

if __name__ == "__main__":
    main()

