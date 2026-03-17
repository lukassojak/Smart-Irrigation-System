FROM python:3.11-slim

WORKDIR /app

COPY smart_irrigation_system ./smart_irrigation_system
COPY runtime ./runtime

COPY smart_irrigation_system/server/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "-m", "smart_irrigation_system.server.main"]