#!/bin/bash
echo "Setting up the Smart Irrigation System demo environment..."

# --- Python environment ---
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Node + Server dependencies..."
pip install -r requirements_demo.txt

# --- Web UI ---
echo "Installing Web UI dependencies..."
cd ../smart_irrigation_system/web_ui || exit
npm install

echo "All dependencies installed successfully!"
echo "You can now run the demo using: ./run_demo.sh"
