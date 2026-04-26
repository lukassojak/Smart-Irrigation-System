"""
Main entry point for the Smart Irrigation System server application.
Sets up the FastAPI server and integrates the IrrigationServer orchestrator.

Runs with:
uvicorn smart_irrigation_system.server.main:app --reload
"""

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from smart_irrigation_system.__version__ import __version__
from smart_irrigation_system.server.core.server_core import IrrigationServer
from smart_irrigation_system.server.api.routes import router as api_router
from smart_irrigation_system.server.configuration.api.v1.routers import router as configuration_router
from smart_irrigation_system.server.runtime.api.routes import router as runtime_router
from smart_irrigation_system.server.runtime.services.live_service import initialize_live_store_from_config

from smart_irrigation_system.server.db.session import engine
from sqlmodel import SQLModel
from sqlmodel import Session



# ------------------- FastAPI setup ------------------- #

app = FastAPI(title="Smart Irrigation Server API",
              version=__version__,
                description=(
                    "REST API for the Smart Irrigation System Server. "
                    "Provides endpoints to monitor and control irrigation nodes."
                )
            )

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")
app.include_router(configuration_router, prefix="/api/v1")
app.include_router(runtime_router, prefix="/api/v1/runtime")

SQLModel.metadata.create_all(bind=engine)


def _ensure_node_config_sync_status_column() -> None:
    """MVP compatibility migration for existing SQLite databases."""
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(node)"))
        columns = {row[1] for row in rows}
        if "config_sync_status" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE node ADD COLUMN config_sync_status TEXT NOT NULL DEFAULT 'PENDING'"
                )
            )


def _ensure_node_hardware_uid_column() -> None:
    """Compatibility migration for the node hardware_uid pairing column."""
    with engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(node)"))
        columns = {row[1] for row in rows}
        if "hardware_uid" not in columns:
            conn.execute(text("ALTER TABLE node ADD COLUMN hardware_uid TEXT"))

        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_node_hardware_uid ON node(hardware_uid)"
            )
        )


# ------------------- Server Orchestrator ------------------- #

server = IrrigationServer()

@app.on_event("startup")    # replace with lifespan in future
def on_startup():
    """Starts the orchestrator during FastAPI server startup."""
    app.logger = getattr(app, "logger", None)
    _ensure_node_config_sync_status_column()
    _ensure_node_hardware_uid_column()
    with Session(engine) as session:
        initialize_live_store_from_config(session)

    print("[Startup] Launching IrrigationServer orchestrator...")
    server.start()
    print("[Startup] IrrigationServer is running.")


@app.on_event("shutdown")   # replace with lifespan in future
def on_shutdown():
    """Stops the orchestrator during FastAPI server shutdown."""
    print("[Shutdown] Stopping IrrigationServer...")
    server.stop()
    print("[Shutdown] Server stopped cleanly.")


# ------------------- Dev Entry Point ------------------- #

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "smart_irrigation_system.server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
