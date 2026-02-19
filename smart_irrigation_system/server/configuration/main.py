from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from smart_irrigation_system.server.configuration.api.v1.routers import router as api_router
from smart_irrigation_system.server.db.session import engine
from sqlmodel import SQLModel

app = FastAPI(title="Node Manager API")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLModel.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")