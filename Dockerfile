
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN ansible-galaxy collection install nokia.srlinux

COPY get_config.py .
COPY check_compliance.py .
COPY golden-config-rules.yml .
COPY inventory.yml .
COPY ansible_inventory.ini .
COPY fix_logging.yml .
COPY ansible.cfg .

CMD ["sh", "-c", "python3 get_config.py && python3 check_compliance.py"]
