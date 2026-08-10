from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from backend.app.api.auth import router as auth_router
from backend.app.api.openai import router as openai_router
from backend.app.api.health import router as health_router
from backend.app.api.api_keys import router as api_keys_router
from backend.app.api.wallet import router as wallet_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.admin import router as admin_router

app = FastAPI(title="Sowaa API", version="1.0.0")

# Security: CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_keys_router)
app.include_router(wallet_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(openai_router)
