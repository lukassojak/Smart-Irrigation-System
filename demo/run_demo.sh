#!/bin/bash
# ============================================================
# Smart Irrigation System – Local Demo Runner
# ============================================================

set -e
echo "Starting Smart Irrigation System demo..."

# --- Paths ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$BASE_DIR")"
VENV_DIR="$BASE_DIR/venv"
NODE_DIR="$REPO_ROOT/smart_irrigation_system/node"
SERVER_DIR="$REPO_ROOT/smart_irrigation_system/server"
WEB_DIR="$REPO_ROOT/web_ui"

# --- Activate venv ---
if [ -d "$VENV_DIR" ]; then
  echo "Activating Python virtual environment..."
  source "$VENV_DIR/bin/activate"
else
  echo "Virtual environment not found! Please run install_demo.sh first."
  exit 1
fi

# --- Detect if GUI and gnome-terminal available ---
HAS_GNOME_TERMINAL=false

if command -v gnome-terminal >/dev/null 2>&1; then
  # Check if running in GUI (X11/Wayland)
  if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    HAS_GNOME_TERMINAL=true
  else
    echo "gnome-terminal found, but no display session detected (likely WSL or SSH)."
    echo "Falling back to background mode."
  fi
else
  echo "gnome-terminal not found, running in background mode."
fi

# --- Start FastAPI Server ---
if $HAS_GNOME_TERMINAL; then
  echo "Launching FastAPI Server in new terminal..."
  gnome-terminal -- bash -c "cd '$SERVER_DIR' && source '$VENV_DIR/bin/activate' && python -m smart_irrigation_system.server.main; exec bash"
else
  echo "Starting FastAPI Server (background)..."
  (cd "$SERVER_DIR" && python -m smart_irrigation_system.server.main > "$BASE_DIR/server.log" 2>&1 &) 
fi

# --- Start Node ---
if $HAS_GNOME_TERMINAL; then
  echo "Launching Node in new terminal..."
  gnome-terminal -- bash -c "cd '$NODE_DIR' && source '$VENV_DIR/bin/activate' && python -m smart_irrigation_system.node.main; exec bash"
else
  echo "Starting Node (background)..."
  (cd "$NODE_DIR" && python -m smart_irrigation_system.node.main > "$BASE_DIR/node.log" 2>&1 &) 
fi

# --- Start Web UI ---
if [ -d "$WEB_DIR" ]; then
  if $HAS_GNOME_TERMINAL; then
    echo "Launching Web UI in new terminal..."
    gnome-terminal -- bash -c "cd '$WEB_DIR' && npm run dev; exec bash"
  else
    echo "Starting Web UI (background)..."
    (cd "$WEB_DIR" && npm run dev > "$BASE_DIR/web.log" 2>&1 &)
  fi
else
  echo "Web UI directory not found at $WEB_DIR"
fi

echo
echo "All components started!"
echo "Server API:   http://127.0.0.1:8000/docs"
echo "Web Dashboard: http://localhost:3000"
echo
if $HAS_GNOME_TERMINAL; then
  echo "Each component is running in its own terminal window."
else
  echo "Logs are written to: $BASE_DIR/server.log, $BASE_DIR/node.log, $BASE_DIR/web.log"
fi
echo
read -p "Press [ENTER] to stop demo..." || true
pkill -f smart_irrigation_system || true
echo "Demo stopped."
