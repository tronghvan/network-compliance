# Network Compliance & Drift Detection System

Automated detection and remediation of network configuration drift — inspired by PCI-DSS/ISO 27001 compliance requirements in banking environments.

## Stack

Containerlab (Nokia SR Linux) · Python · Netmiko · Ansible · Docker · Kubernetes · Helm · GitHub Actions

## Architecture

```
Containerlab → Netmiko (SSH) → Compliance Check (YAML rules)
     → Ansible (auto-remediate critical) → Docker → K8s CronJob (via Helm)
     → GitHub Actions CI/CD (build → push → deploy)
```

## How It Works

- Golden config rules defined declaratively in YAML, tagged by severity.
- Compliance checker pulls live config via SSH, flags drift, exits non-zero on failure (no silent false-positives).
- Critical violations auto-remediated via Ansible; high-risk changes (routing/ACL) left for manual review.
- Packaged as a Docker image, scheduled via K8s CronJob, deployed through a Helm chart supporting multiple environments (dev/prod).
- GitHub Actions automates build → push → deploy on every commit, using a self-hosted runner for cluster access.

## Quick Start

```bash
sudo containerlab deploy --topo containerlab/topology.clab.yaml
python3 get_config.py && python3 check_compliance.py
ansible-playbook -i ansible_inventory.ini fix_logging.yml
docker build -t network-compliance:v0.1 .
helm install compliance-dev ./network-compliance-chart
```
