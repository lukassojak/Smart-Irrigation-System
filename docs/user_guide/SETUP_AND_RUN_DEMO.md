# Smart Irrigation System – Local All-in-One Demo Setup  
**Applies to:** Smart Irrigation System v0.9+ (Node + Server + Web UI prototype)  

This guide explains how to **run the full Smart Irrigation System demo locally on a single computer**,  
including all three layers – **Node**, **Server**, and **Web UI** – without any external hardware.

The demo allows you to test the complete architecture and observe MQTT communication and REST API integration in action.

---

## Overview
In this demo:
- All three layers (Node, Server, Web UI) run on your PC.  
- Communication is handled locally using a **Mosquitto MQTT broker**.
- The demo simulates an irrigation node, the central server, and a simple dashboard as a prototype of the Web UI.

**Architecture (local setup):**

```
[Node (simulated)] <--> MQTT <--> [Server (local)] <--> REST API <--> [Web UI (local)]
```

---

## Prerequisites

### System Requirements
- **Python** ≥ 3.10  
- **Node.js** ≥ 18 (LTS)  
- **Mosquitto MQTT Broker**  
- **Git**

---

## Simplified Installation (Recommended)

The easiest way to install and run the full demo is using the prepared shell scripts.

### 1️⃣ Install all dependencies
```bash
cd demo
./install_demo.sh
```

This script will:
- Create a Python virtual environment (`venv`)
- Install all required Python dependencies (for Server and Node simulation) from `requirements_demo.txt`
- Install all Web UI dependencies via `npm install`

### 2️⃣ Run the demo
```bash
./run_demo.sh
```

This script will:
- Start a local Mosquitto MQTT broker (if not already running)
- Launch the simulated Node, Server, and Web UI
- Each component opens in a separate terminal window

### 3️⃣ Access the Web UI
After running the demo, open your web browser and navigate to:
```
http://localhost:3000
```

**You should see the Smart Irrigation System dashboard displaying simulated data.**

---

## Manual Installation
If you prefer to set up each component manually, follow the steps below.

### 1️⃣ Create Python Virtual Environment
```bash
cd demo
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 2️⃣ Install Python Dependencies
Install all required Python packages for Node and Server:
```bash
pip install -r requirements_demo.txt
```

*This combines both `node/requirements.txt` and `server/requirements.txt`.*

### 3️⃣ Install Web UI Dependencies
```bash
cd ../web_ui
npm install
cd ../demo
```

### 4️⃣ Start Mosquitto MQTT Broker
Make sure Mosquitto is installed and running:
```bash
sudo service mosquitto start
```
or to run it manually:
```bash
mosquitto -v
```

*Default configuration uses localhost:1883.*

### 5️⃣ Run the Server
In one terminal, start the Server:
```bash
source venv/bin/activate  # Activate the virtual environment
python -m smart_irrigation_system.server.main
```
*Check the API is available at* `http://localhost:8000/docs`.

### 6️⃣ Run the Simulated Node
In another terminal, start the simulated Node:
```bash
source venv/bin/activate  # Activate the virtual environment
python -m smart_irrigation_system.node.main
```
*You should see Node debug CLI running.*

### 7️⃣ Run the Web UI
In a third terminal, start the Web UI:
```bash
cd ../web_ui
npm run dev
```
Once running, visit:

```
http://localhost:3000
```

**You should see the Smart Irrigation System dashboard displaying simulated data.**

---

## Verify the Setup

Once all components are running:

| Component        | Expected Behavior                                                  |
|------------------|--------------------------------------------------------------------|
| Simulated Node   | Publishes status messages to MQTT, responds to commands.           |
| Server           | Receives MQTT messages, exposes REST API.                          |
| Web UI           | Displays connected nodes, their status, allows irrigation control. |

You can trigger irrigation actions via the Web UI and observe the Node responding accordingly in its CLI:
**- Start irrigation** → Sends `/start_irrigation` request to Node.
**- Stop irrigation** → Sends `/stop_irrigation` request to Node.
**- Refresh status** → fetches `/nodes` via REST.

> In current implementation, the Web UI polls the fresh status every 3 seconds. The server updates the Node status cache every 10 seconds. Maximum delay for status updates is around 13 seconds.