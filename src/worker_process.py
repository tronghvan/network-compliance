import redis
import json
import re
import sys
import time
from rule_loader import load_all_rules
from prometheus_client import start_http_server, Counter, Histogram




events_processed = Counter(
    "compliance_events_processed_total",
    "Total number of events processed",
    ["worker_id", "severity"]
)

events_failed = Counter(
    "compliance_events_failed_total",
    "Total number of events that have been handled",
    ["worker_id"]
)

processing_time = Histogram(
    "compliance_event_processing_seconds",
    "Event processing time",
    ["worker_id"]
)

queue_length = Counter(
    "compliance_queue_pulled_total",
    "Total number of times items were retrieved from the queue",
    ["worker_id"]
)


r = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=None, socket_connect_timeout=5)
QUEUE_NAME = "compliance_events"

def check_event_against_rules(path, val, rules):
    results = []
    for rule in rules:
        event_check = rule.get("check", {}).get("event", {})
        if not event_check:
            continue
        if event_check.get("path_contains") and event_check["path_contains"] not in path:
            continue

        if "expected_value_contains" in event_check:
            match = re.search(r"host=([\d.]+)", path)
            actual_host = match.group(1) if match else None
            expected = event_check["expected_value_contains"]
            if actual_host != expected:
                results.append({"severity": rule["severity"],
                                 "message": f"{rule['metadata']['rule_id']} -- thuc te: {actual_host}, mong doi: {expected}"})
            else:
                results.append({"severity": "ok",
                                 "message": f"{rule['metadata']['rule_id']} -- OK"})
    return results

def main(worker_id):
    all_rules = load_all_rules()

    
    metrics_port = 8000 + int(worker_id)
    start_http_server(metrics_port)
    print(f"[Worker-{worker_id}] Metrics is currently serving at the gate {metrics_port}")
    print(f"[Worker-{worker_id}] Ready for implementation from Redis queue...")

    while True:
        try:
            _, raw_event = r.blpop(QUEUE_NAME)
            queue_length.labels(worker_id=worker_id).inc()

            start_time = time.time()
            event = json.loads(raw_event)

            device_name = event["device_name"]
            dev_group = event.get("dev_group", "default")
            path = event["path"]
            val = event["val"]
            applicable_rules = []
            for r_item in all_rules:
                rule_groups = r_item.get("metadata", {}).get("applies_to", {}).get("device_group")
                if not rule_groups or dev_group in rule_groups:
                    applicable_rules.append(r_item)

            results = check_event_against_rules(path, val, applicable_rules)
            print(f"\n[Worker-{worker_id}] Event handling from {device_name}")
            print(f"Path: {path}")
            for res in results:
                print(f"  [{res['severity'].upper()}] {res['message']}")
                events_processed.labels(worker_id=worker_id, severity=res["severity"]).inc()

            elapsed = time.time() - start_time
            processing_time.labels(worker_id=worker_id).observe(elapsed)

        except Exception as e:
            print(f"[Worker-{worker_id}] Error event handling : {e}")
            events_failed.labels(worker_id=worker_id).inc()

if __name__ == "__main__":
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    main(worker_id)
