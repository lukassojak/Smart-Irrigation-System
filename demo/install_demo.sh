#!/bin/bash
# ============================================================
# Smart Irrigation System – Local Demo Installer
# Tested on Linux / WSL / macOS
# ============================================================

set -e  # stop on first error
echo "Setting up Smart Irrigation System demo environment..."

# --- Helper function ---
function check_cmd {
  command -v "$1" >/dev/null 2>&1 || { echo "  Missing: $1"; MISSING="$MISSING $1"; }
}

# --- Check required tools ---
echo "1. Checking environment..."
MISSING=""
check_cmd python3
check_cmd pip
check_cmd npm
check_cmd mosquitto
if [ ! -z "$MISSING" ]; then
  echo "   Missing required tools: $MISSING"
  echo "   Please install them manually before running this script."
  echo "   Example (Debian/Ubuntu): sudo apt install python3 python3-pip python3-venv npm mosquitto"
  exit 1
fi

# --- Install gnome-terminal if available ---
if [ -f /etc/debian_version ]; then
  echo "2. Ensuring GNOME terminal availability..."
  sudo apt-get install -y gnome-terminal || echo "  Skipping, not available in this environment."
fi

# --- Create Python virtual environment ---
echo "3. Creating Python virtual environment..."
if ! python3 -m venv venv; then
  echo "   python3-venv not found. Trying system install..."
  if [ -f /etc/debian_version ]; then
    echo "     Run: sudo apt install python3-venv"
  elif [ "$(uname)" == "Darwin" ]; then
    echo "     Run: brew install python@3"
  else
    echo "   Cannot automatically install python3-venv. Please install manually."
  fi
  exit 1
fi

source venv/bin/activate

# --- Install Python dependencies ---
echo "4. Installing Python dependencies (Node + Server)..."
if [ -f "requirements_demo.txt" ]; then
  pip install -r requirements_demo.txt
else
  echo "   requirements_demo.txt not found, skipping Python installation."
fi

# --- Install Web UI dependencies ---
if [ -d "../web_ui" ]; then
  echo "5. Installing Web UI dependencies (React)..."
  cd ../web_ui
  npm install
  cd ../demo
else
  echo "   Web UI folder not found, skipping npm install."
fi

echo "Installation complete!"
echo "You can now start the demo with:"
echo "   ./run_demo.sh"