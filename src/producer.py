import redis
import json
import yaml 
import threading
from pathlib import Path
from pygnmi.client import gNMIclient


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = BASE_DIR / "inventory" / "inventory.yml"

r = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=None, socket_connect_timeout=5)
QUEUE_NAME = "compliance_events"

def load_inventory(path=DEFAULT_INVENTORY):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("devices", [])

def gnmi_listener(device_conf, device_name, dev_group):
    with gNMIclient(**device_conf) as gc:
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
                print(f"{device_name}: Synchronization is complete")
                continue
            if not sync_completed:
                continue

            update_data = update.get("update", {})
            for change in update_data.get("update", []):
                path = change.get("path", "")
                val = change.get("val", {})

                event = {
                    "device_name": device_name,
                    "dev_group": dev_group,
                    "path": path,
                    "val": val
                }
                
                r.rpush(QUEUE_NAME, json.dumps(event))
                print(f"[Producer] Has pushed the event from {device_name} in Redis queue")

if __name__ == "__main__":
    
    devices = load_inventory()
    
    if not devices:
        print("[!] No devices found in inventory.yml!")
        exit(1)

    print(f"Loaded {len(devices)} devices from  inventory. Initiating threads producer...")

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
        
        t = threading.Thread(target=gnmi_listener, args=(device_conf, device_name, dev_group), daemon=True)
        t.start()
        listener_threads.append(t)
        print(f"Listening devices: {device_name} [Group: {dev_group}] (Host: {dev['host']})")

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBuild a successful product")
