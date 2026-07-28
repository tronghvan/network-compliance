#!/usr/bin/env python3
import yaml
from netmiko import ConnectHandler

def load_inventory(path="inventory.yml"):
    with open(path, "r") as f:
        data =  yaml.safe_load(f)
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
        return output
    except Exception as e:
        print(f"[LOI] Connectn't {device['name']}: {e}")
        return None
def main():
    devices =  load_inventory()
    for device in devices:
        print(f"--- getting config from {device['name']} ({device['host']}) ---")
        config = get_running_config(device)
        if config:
            filename = f"configs_actual_{device['name']}.txt"
            with open(filename, "w") as f:
                f.write(config)
            print(f"Saved in {filename}\n")
        else:
            print(f"skip {device['name']} error connect\n")
if __name__ == "__main__":
    main()
