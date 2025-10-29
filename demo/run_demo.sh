#!/bin/bash
echo "Starting Smart Irrigation System demo..."

# Ensure MQTT broker is running
if ! nc -z localhost 1883; then
  echo "Mosquitto broker not found on localhost:1883"
  echo "Starting local broker (background)..."
  mosquitto -v > /dev/null 2>&1 &
  sleep 2
fi

# Start server
echo "Starting FastAPI Server..."
gnome-terminal -- bash -c "source venv/bin/activate && python -m smart_irrigation_system.server.main; exec bash"

# Start node
echo "Starting simulated Node..."
gnome-terminal -- bash -c "source venv/bin/activate && python -m smart_irrigation_system.node.main; exec bash"

# Start web UI
echo "Starting Web Dashboard..."
cd smart_irrigation_system/web_ui || exit
npm run dev
