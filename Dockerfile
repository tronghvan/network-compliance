
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN ansible-galaxy collection install nokia.srlinux

COPY src/ ./src/
COPY inventory/inventory.yml ./inventory/
COPY inventory/ansible_inventory.ini ./inventory/
COPY rules/ ./rules/
COPY legacy-rules/ ./legacy-rules/
COPY ansible/fix_logging.yml ./ansible/
COPY ansible.cfg .

RUN mkdir -p /app/outputs

WORKDIR /app/src

CMD ["sh", "-c", "python3 get_config.py && python3 check_compliance.py"]
