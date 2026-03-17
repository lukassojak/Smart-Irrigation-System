FROM python:3.11-slim

WORKDIR /app

COPY smart_irrigation_system ./smart_irrigation_system
COPY runtime ./runtime

COPY smart_irrigation_system/node/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "smart_irrigation_system.node.main"]