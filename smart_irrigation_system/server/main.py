"""
Main entry point for the Smart Irrigation System server application.
Sets up the FastAPI server and integrates the IrrigationServer orchestrator.

Runs with:
uvicorn smart_irrigation_system.server.main:app --reload
"""

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from smart_irrigation_system.__version__ import __version__
from smart_irrigation_system.server.core.server_core import IrrigationServer
from smart_irrigation_system.server.api.routes import router as api_router
from smart_irrigation_system.server.configuration.api.v1.routers import router as configuration_router
from smart_irrigation_system.server.runtime.api.routes import router as runtime_router

from smart_irrigation_system.server.db.session import engine
from sqlmodel import SQLModel



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


# ------------------- Server Orchestrator ------------------- #

server = IrrigationServer(broker_host="localhost", broker_port=1883)

@app.on_event("startup")    # replace with lifespan in future
def on_startup():
    """Starts the orchestrator during FastAPI server startup."""
    app.logger = getattr(app, "logger", None)
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
