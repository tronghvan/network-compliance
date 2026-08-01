#!/usr/bin/env python3
import yaml
import time
from netmiko import ConnectHandler
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = BASE_DIR / "inventory" / "inventory.yml"
OUTPUT_DIR = BASE_DIR / "outputs"
def load_inventory(path=DEFAULT_INVENTORY):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data["devices"]

def get_running_config(device):
    connection_params = {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": device["username"],
        "password": device["password"],
    }
    try:
        conn = ConnectHandler(**connection_params)
        output = conn.send_command("info")
        conn.disconnect()
        return device, output
    except Exception as e:
        print(f"[LOI] Connectn't {device['name']}: {e}")
        return device, None

def process_result(device, config):
    if config:
        filename = OUTPUT_DIR / f"configs_actual_{device['name']}.txt"
        with open(filename, "w") as f:
            f.write(config)
        print(f"Saved in {filename}")
    else:
        print(f"skip {device['name']} error connect")

def main():
    devices = load_inventory()
    max_workers = 20   #start

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(get_running_config, d) for d in devices]
        for future in as_completed(futures):
            device, config = future.result()
            process_result(device, config)

    elapsed = time.time() - start_time
    print(f"\nTotal processing time: {elapsed:.2f} second with {max_workers} workers")

if __name__ == "__main__":
    main()
