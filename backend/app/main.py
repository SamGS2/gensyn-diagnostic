from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gensyn Diagnostic Tool",
    description="Framework-based diagnostic for identifying organizational stuck points",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://diagnostic.gensyn.co",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routes.diagnostic import router as diagnostic_router
from app.routes.sessions import router as sessions_router
from app.routes.notifications import router as notifications_router
from app.routes.admin import router as admin_router

app.include_router(diagnostic_router)
app.include_router(sessions_router)
app.include_router(notifications_router)
app.include_router(admin_router)

if not os.getenv("SERPAPI_KEY"):
    logger.warning("SERPAPI_KEY is not set; company API fallback lookup is disabled.")
if not os.getenv("RESEND_API_KEY"):
    logger.warning("RESEND_API_KEY is not set; Resend onboarding email endpoint is disabled.")


@app.get("/")
async def root():
    return {"status": "ok", "service": "Gensyn Diagnostic Tool"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
