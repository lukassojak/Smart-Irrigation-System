# Smart Irrigation System – Server & Web UI Setup Guide

This document explains how to **install and run the Server (FastAPI backend)** and the **Web UI (React + Vite frontend)** on a single device for demonstration and testing purposes.
It also outlines the future full architecture when deployed across multiple devices (Server ↔ Node network).

---

## Overview

The Smart Irrigation System consists of three main layers:

1. **Node (Edge Device)** – runs irrigation logic locally on Raspberry Pi Zero.  
2. **Server (Backend)** – orchestrates nodes, communicates via MQTT, exposes REST API.  
3. **Web UI (Frontend)** – user dashboard for monitoring and control.

This guide covers **Server** and **Web UI** setup for local demonstration and testing (both running on the same device).

---

## 1. Requirements

### General prerequisites
- **Python 3.10+**
- **Node.js 20+** (includes NPM)
- **MQTT broker** (e.g., Mosquitto)
- **Git** (for cloning the repository)

---

## 2. Clone the repository

*If not already done.*

```bash
git clone https://github.com/lukassojak/Smart-Irrigation-System.git
cd Smart-Irrigation-System
```

---

## 3. Setup the server (FastAPI backend)

*Virtual environment is not used here, but recommended in future.*

### 3.1 Install Python dependencies

```bash
pip install -r server/requirements.txt
```

### 3.2 Run the server (development mode)

```bash
uvicorn smart_irrigation_system.server.main:app --reload --host 0.0.0.0 --port 8000
```

The server provides:
- REST API at `http://localhost:8000`
- Swagger UI (API docs) at `http://localhost:8000/docs`
- (after Web UI build) Serves the dashboard at `/`

---

## 4. Setup the Web UI (React + Vite frontend)

### 4.1 Install Node.js dependencies

```bash
cd web_ui
npm install
```

Dependencies are defined in `web_ui/package.json`.

### 4.2 Start development server

```bash
npm run dev
```

### 4.3 Access the Web UI

Access the Web UI at `http://localhost:5173`.

The development server proxies API requests to the FastAPI backend (configured in `web_ui/vite.config.js`).

### 4.4 Build for production

To build the Web UI for production and serve it via the FastAPI server:

```bash
npm run build
```

This generates static files in `web_ui/dist` which FastAPI can serve.

---

## 5. Serving the Built Frontend via FastAPI

Once you have run `npm run build`, FastAPI can serve the frontend directly. The following code (already present or to be added once) in `smart_irrigation_system/server/main.py` mounts the static files:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import os

app = FastAPI()

DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "web_ui", "dist")

if os.path.isdir(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")

@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "UI build not found"}
```

---

## 6. Run both server and Web UI together (local demo)

In two separate terminal windows/tabs:

### Terminal 1: Start the FastAPI server

```bash
uvicorn smart_irrigation_system.server.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Start the Web UI development server

```bash
cd web_ui
npm run dev
```

Then open the Web UI at `http://localhost:5173`.

---

## 7. Future full architecture

When the system is split across multiple devices:

```
[Raspberry Pi Zero]       [Raspberry Pi 4 or PC]        [User Device]
       Node   <──MQTT──>        Server (FastAPI)  <──REST──>   Web UI
                             (also hosts static build)
```

## 8. File references

`server/requirements.txt` - Python backend dependencies
`web_ui/package.json` - Node.js frontend dependencies
`vite.config.js` - Vite configuration for API proxying
`server/main.py` - FastAPI server main application file
`server/api/routes.py` - REST API endpoints

