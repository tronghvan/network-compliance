import time
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PLAYBOOK = BASE_DIR / "ansible" / "fix_logging.yml"
DEFAULT_ANSIBLE_INVENTORY = BASE_DIR / "inventory" / "ansible_inventory.ini"


MAX_AUTO_FIX_PER_WINDOW = 3
TIME_WINDOW_SECONDS = 60


remediation_history = []

def can_auto_remediate():
    
    now = datetime.now()
    cutoff = now - timedelta(seconds=TIME_WINDOW_SECONDS)

    
    recent = [t for t in remediation_history if t > cutoff]
    remediation_history[:] = recent

    if len(recent) >= MAX_AUTO_FIX_PER_WINDOW:
        return False, f"Limit has been reached {MAX_AUTO_FIX_PER_WINDOW} aumation in {TIME_WINDOW_SECONDS}s"

    return True, None

def record_remediation_attempt():
    remediation_history.append(datetime.now())

def run_remediation_playbook(device_name, playbook_path, inventory_path):
    
    print(f"[Remediation] Start fixing on {device_name}...")

    result = subprocess.run(
        ["ansible-playbook", "-i", inventory_path, playbook_path,
         "--limit", device_name],
        capture_output=True,
        text=True,
        timeout=30
    )

    success = result.returncode == 0
    return {
        "device": device_name,
        "success": success,
        "stdout": result.stdout[-500:] if result.stdout else "",
        "stderr": result.stderr[-500:] if result.stderr else ""
    }

def attempt_remediation(device_name, rule, playbook_path=DEFAULT_PLAYBOOK, inventory_path=DEFAULT_ANSIBLE_INVENTORY):
 
    rule_id = rule.get("metadata", {}).get("rule_id", "UNKNOWN")

    
    if not rule.get("auto_remediate", False):
        print(f"[Remediation] Rule {rule_id} Automatic correction is not allowed")
        return {"status": "skipped", "reason": "auto_remediate=false"}

    
    allowed, reason = can_auto_remediate()
    if not allowed:
        print(f"[Remediation] Reject automatic correction {device_name}: {reason}")
        print(f"[Remediation] Manual operator review required")
        return {"status": "blocked", "reason": reason}

    
    record_remediation_attempt()
    result = run_remediation_playbook(device_name, playbook_path, inventory_path)

    if result["success"]:
        print(f"[Remediation] Success: {device_name} The issue has been resolved according to the rule. {rule_id}")
    else:
        print(f"[Remediation] Failure: {device_name} - {result['stderr']}")

    return {"status": "executed", "result": result}
